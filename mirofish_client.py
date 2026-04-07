#!/usr/bin/env python3
"""
mirofish_client.py — MiroFish API Client

Client for the local MiroFish Flask API.
Provides methods to run social simulations via the API.
"""

import time
import requests
import logging
import subprocess
import re

logger = logging.getLogger(__name__)


class MiroFishClient:
    """Client for the MiroFish API."""

    def __init__(self, base_url: str = "http://localhost:5001/api"):
        """
        Initialize the MiroFish client.

        Args:
            base_url: Base URL of the MiroFish API (without trailing slash)
        """
        self.base_url = base_url.rstrip("/")
        logger.info(f"[MiroFishClient] Initialized with base URL: {self.base_url}")

    def _check_success(self, response: requests.Response, step_name: str) -> dict:
        """
        Check if the API response indicates success.

        Args:
            response: The requests.Response object
            step_name: Name of the step for logging

        Returns:
            The JSON response data

        Raises:
            RuntimeError: If the response indicates failure
        """
        data = response.json()
        if not data.get("success", False):
            logger.error(f"[MiroFishClient] {step_name} failed: {response.text}")
            raise RuntimeError(f"{step_name} failed: {response.text}")
        return data

    def run_simulation(self, campaign_name: str, context: str) -> dict:
        """
        Run a complete MiroFish simulation.

        This method executes the following steps:
        1. Generate ontology/graph
        2. Build graph
        3. Create simulation
        4. Prepare simulation
        5. Start simulation
        6. Poll for completion
        7. Generate report

        Args:
            campaign_name: Name of the campaign/simulation
            context: Context/requirements for the simulation

        Returns:
            Dictionary containing the simulation results
        """
        # Step 1: Generate ontology
        logger.info("[MiroFishClient] Step 1: Generating ontology...")
        
        # Erstelle die Multipart-Payload
        files = {
            "files": ("brand_context.txt", context.encode('utf-8'), "text/plain")
        }
        data = {
            "simulation_requirement": context,
            "llm_model": "extra.Qwen2.5-14B-Instruct-Q4_K_M.gguf",
            "embedding_model": "extra.bge-m3-FP16.gguf"
        }
        
        response = requests.post(
            f"{self.base_url}/graph/ontology/generate",
            data=data,
            files=files
        )
        data = self._check_success(response, "Ontology Generation")
        project_id = data["data"]["project_id"]
        logger.info(f"[MiroFishClient] Project ID: {project_id}")

        # Step 2: Build graph
        logger.info("[MiroFishClient] Step 2: Building graph...")
        response = requests.post(
            f"{self.base_url}/graph/build",
            json={
                "project_id": project_id,
                "llm_model": "extra.Qwen2.5-14B-Instruct-Q4_K_M.gguf",
                "embedding_model": "extra.bge-m3-FP16.gguf"
            }
        )
        data = self._check_success(response, "Graph Build")
        task_id = data["data"]["task_id"]
        logger.info(f"[MiroFishClient] Graph build task ID: {task_id}")
        
        # Poll for graph build completion
        graph_id = self._poll_graph_task(task_id, project_id)
        logger.info(f"[MiroFishClient] Graph ID: {graph_id}")

        # Step 3: Create simulation
        logger.info("[MiroFishClient] Step 3: Creating simulation...")
        response = requests.post(
            f"{self.base_url}/simulation/create",
            json={
                "project_id": project_id,
                "graph_id": graph_id,
                "name": campaign_name,
                "llm_model": "extra.Qwen2.5-14B-Instruct-Q4_K_M.gguf",
                "embedding_model": "extra.bge-m3-FP16.gguf"
            }
        )
        data = self._check_success(response, "Simulation Creation")
        simulation_id = data["data"]["simulation_id"]
        logger.info(f"[MiroFishClient] Simulation ID: {simulation_id}")

        # Step 4: Prepare simulation
        logger.info("[MiroFishClient] Step 4: Preparing simulation...")
        response = requests.post(
            f"{self.base_url}/simulation/prepare",
            json={"simulation_id": simulation_id}
        )
        self._check_success(response, "Simulation Preparation")
        
        # Poll for preparation completion
        logger.info("[MiroFishClient] Polling for preparation completion...")
        while True:
            try:
                response = requests.get(f"{self.base_url}/simulation/{simulation_id}")
                data = response.json()
                
                if not data.get("success", False):
                    logger.warning(f"[MiroFishClient] Preparation status check failed: {response.text}")
                    time.sleep(5)
                    continue
                
                status = data["data"].get("status", "")
                logger.info(f"[MiroFishClient] Preparation poll: status = {status}...")
                
                if status == "ready" or status == "prepared":
                    logger.info("[MiroFishClient] Preparation completed successfully")
                    break
                elif status == "preparing":
                    time.sleep(5)  # Wait before next poll
                else:
                    # Unknown status, log full response for debugging
                    logger.error(f"[MiroFishClient] Unexpected status: {status}")
                    logger.error(f"[MiroFishClient] Full response: {response.text}")
                    time.sleep(5)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"[MiroFishClient] Request error during preparation polling: {e}")
                time.sleep(5)

        # Step 5: Start simulation
        logger.info("[MiroFishClient] Step 5: Starting simulation...")
        try:
            response = requests.post(
                f"{self.base_url}/simulation/start",
                json={"simulation_id": simulation_id}
            )
            self._check_success(response, "Simulation Start")
        except RuntimeError as e:
            logger.error(f"[MiroFishClient] Start simulation response: {response.text}")
            raise

        # Step 6: Poll for completion
        logger.info("[MiroFishClient] Step 6: Polling for simulation completion...")
        status = self._poll_simulation(simulation_id)
        logger.info(f"[MiroFishClient] Simulation completed with status: {status}")

        # Step 7: Generate report
        logger.info("[MiroFishClient] Step 7: Generating report...")
        response = requests.post(
            f"{self.base_url}/report/generate",
            json={"simulation_id": simulation_id}
        )
        data = self._check_success(response, "Report Generation")

        # Extract task_id from the initial response (asynchronous generation)
        task_id = data["data"].get("task_id")
        if not task_id:
            logger.error("[MiroFishClient] No task_id in report generation response")
            return data

        logger.info(f"[MiroFishClient] Report generation task_id: {task_id}")
        logger.info("[MiroFishClient] Polling for report generation completion...")

        # Poll for report generation completion
        final_report = self._poll_report_generation(task_id)

        logger.info("[MiroFishClient] Simulation completed successfully")
        return final_report

    def _poll_graph_task(self, task_id: str, project_id: str, poll_interval: int = 60, max_retries: int = 30) -> str:
        """
        Poll the graph task status endpoint until completion.
        
        The task response may contain the graph_id directly, or we need to fetch it
        from the project endpoint as fallback.

        Args:
            task_id: ID of the graph build task to poll
            project_id: ID of the project
            poll_interval: Seconds between status checks
            max_retries: Maximum number of polling attempts

        Returns:
            Final graph_id string

        Raises:
            RuntimeError: If task fails or times out
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/graph/task/{task_id}")
                data = response.json()
                
                if not data.get("success", False):
                    logger.warning(f"[MiroFishClient] Graph task status check failed: {response.text}")
                    continue
                
                status = data["data"].get("status", "")
                logger.info(f"[MiroFishClient] Graph task poll attempt {attempt + 1}/{max_retries}: Status = {status}")
                
                # Check if graph_id is in the task result
                if status == "completed":
                    if "graph_id" in data["data"]:
                        return data["data"]["graph_id"]
                    # Fallback: fetch graph_id from project endpoint
                    logger.info("[MiroFishClient] Task completed, fetching graph_id from project endpoint...")
                    project_response = requests.get(f"{self.base_url}/graph/project/{project_id}")
                    project_data = project_response.json()
                    if not project_data.get("success", False):
                        logger.error(f"[MiroFishClient] Project data: {project_response.text}")
                        raise RuntimeError("Failed to fetch graph_id from project endpoint")
                    if "graph_id" in project_data["data"]:
                        return project_data["data"]["graph_id"]
                    # Log full response for debugging
                    logger.error(f"[MiroFishClient] Project data: {project_response.text}")
                    raise RuntimeError("graph_id not found in project response. See logs for full JSON.")
                
                elif status in ("failed", "error"):
                    raise RuntimeError(f"Graph build failed with status: {status}")
                
                else:
                    # Wait before next poll
                    if attempt < max_retries - 1:
                        time.sleep(poll_interval)
                        
            except requests.exceptions.RequestException as e:
                logger.warning(f"[MiroFishClient] Request error during graph task polling: {e}")
                if attempt < max_retries - 1:
                    time.sleep(poll_interval)
        
        raise RuntimeError(f"Graph task polling timed out after {max_retries} attempts")

    def _check_simulation_log_completed(self, simulation_id: str) -> bool:
        """
        Check if the simulation log indicates completion by looking for the completion message.
        
        Args:
            simulation_id: ID of the simulation
            
        Returns:
            True if the completion message is found, False otherwise
        """
        try:
            # Build the docker command to check for the completion message
            command = [
                "docker", "exec", "mirofish-offline",
                "grep", "-q", "Simulation loop completed!",
                f"/app/backend/uploads/simulations/{simulation_id}/simulation.log"
            ]
            # Run the command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
            # Return code 0 means the string was found
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("[MiroFishClient] Docker command not found. Skipping log check.")
            return False
        except subprocess.SubprocessError as e:
            logger.warning(f"[MiroFishClient] Error checking simulation log: {e}")
            return False
        except Exception as e:
            logger.warning(f"[MiroFishClient] Unexpected error checking simulation log: {e}")
            return False

    def _poll_simulation(self, simulation_id: str, poll_interval: int = 60, max_retries: int = 90) -> str:
        """
        Poll the simulation status endpoint until completion.

        Args:
            simulation_id: ID of the simulation to poll
            poll_interval: Seconds between status checks
            max_retries: Maximum number of polling attempts

        Returns:
            Final status string ("completed")

        Raises:
            RuntimeError: If simulation fails or times out
        """
        for attempt in range(max_retries):
            try:
                # First, check the simulation log directly in Docker container
                if self._check_simulation_log_completed(simulation_id):
                    logger.info(f"[MiroFishClient] Log check confirmed simulation completion for {simulation_id}")
                    return "completed"
                
                response = requests.get(f"{self.base_url}/simulation/{simulation_id}")
                data = response.json()

                if not data.get("success", False):
                    logger.warning(f"[MiroFishClient] Status check failed: {response.text}")
                    continue

                status = data["data"]["status"]
                logger.info(f"[MiroFishClient] Poll attempt {attempt + 1}/{max_retries}: Status = {status}")

                if status == "completed":
                    return status
                elif status in ("failed", "error"):
                    raise RuntimeError(f"Simulation failed with status: {status}")
                else:
                    # Wait before next poll
                    if attempt < max_retries - 1:
                        time.sleep(poll_interval)

            except requests.exceptions.RequestException as e:
                logger.warning(f"[MiroFishClient] Request error during polling: {e}")
                if attempt < max_retries - 1:
                    time.sleep(poll_interval)

        raise RuntimeError(f"Simulation polling timed out after {max_retries} attempts")

    def _score_with_llm(self, markdown_content: str) -> dict:
        """
        Send markdown content to local LLM (Lemonade) for scoring.

        Args:
            markdown_content: The markdown report content to score

        Returns:
            Dictionary with scores: positive_sentiment, negative_sentiment, virality_score, controversy_risk
        """
        system_prompt = """Du bist ein Datenanalyst. Lies den folgenden Report und extrahiere exakt vier Metriken zwischen 0.0 und 1.0 als reines JSON-Objekt ohne Markdown-Formatierung: positive_sentiment, negative_sentiment, virality_score, controversy_risk."""
        
        payload = {
            "model": "extra.Qwen2.5-14B-Instruct-Q4_K_M.gguf",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": markdown_content}
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        try:
            response = requests.post(
                "http://127.0.0.1:8888/v1/chat/completions",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Try to parse JSON from response
            import json as json_module
            try:
                # Try direct JSON parsing
                scores = json_module.loads(content)
                return {
                    "positive_sentiment": float(scores.get("positive_sentiment", 0.5)),
                    "negative_sentiment": float(scores.get("negative_sentiment", 0.5)),
                    "virality_score": float(scores.get("virality_score", 0.5)),
                    "controversy_risk": float(scores.get("controversy_risk", 0.5))
                }
            except (json_module.JSONDecodeError, ValueError):
                # Fallback: try to find JSON in response
                import re
                json_match = re.search(r'\{[^{}]*\}', content)
                if json_match:
                    try:
                        scores = json_module.loads(json_match.group())
                        return {
                            "positive_sentiment": float(scores.get("positive_sentiment", 0.5)),
                            "negative_sentiment": float(scores.get("negative_sentiment", 0.5)),
                            "virality_score": float(scores.get("virality_score", 0.5)),
                            "controversy_risk": float(scores.get("controversy_risk", 0.5))
                        }
                    except (json_module.JSONDecodeError, ValueError):
                        pass
                
                # Final fallback
                logger.warning("[MiroFishClient] LLM response parsing failed, using fallback values")
                return {
                    "positive_sentiment": 0.5,
                    "negative_sentiment": 0.5,
                    "virality_score": 0.5,
                    "controversy_risk": 0.5
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[MiroFishClient] LLM API request failed: {e}")
            return {
                "positive_sentiment": 0.5,
                "negative_sentiment": 0.5,
                "virality_score": 0.5,
                "controversy_risk": 0.5
            }
        except Exception as e:
            logger.error(f"[MiroFishClient] Unexpected error during LLM scoring: {e}")
            return {
                "positive_sentiment": 0.5,
                "negative_sentiment": 0.5,
                "virality_score": 0.5,
                "controversy_risk": 0.5
            }

    def _poll_report_generation(self, task_id: str, poll_interval: int = 60, max_retries: int = 90) -> dict:
        """
        Poll the report generation status endpoint until completion.

        Args:
            task_id: ID of the report generation task to poll
            poll_interval: Seconds between status checks
            max_retries: Maximum number of polling attempts

        Returns:
            Final report data dictionary with LLM scores

        Raises:
            RuntimeError: If report generation fails or times out
        """
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/report/generate/status",
                    json={"task_id": task_id}
                )

                if response.status_code != 200:
                    logger.error(f"[MiroFishClient] API error {response.status_code}. Raw response: {response.text}")

                try:
                    data = response.json()
                except ValueError:
                    logger.error(f"[MiroFishClient] Failed to parse JSON. Raw API response: '{response.text}'")
                    time.sleep(poll_interval)
                    continue

                if not data.get("success", False):
                    logger.warning(f"[MiroFishClient] Report status check failed: {response.text}")
                    continue

                status = data["data"].get("status", "")
                logger.info(f"[MiroFishClient] Report generation poll attempt {attempt + 1}/{max_retries}: Status = {status}")

                if status in ("completed", "success"):
                    # Get report_id from response
                    report_id = data["data"].get("result", {}).get("report_id")
                    if not report_id:
                        logger.error("[MiroFishClient] No report_id in response")
                        return data["data"].get("report", data["data"])
                    
                    # Fetch the report content
                    report_response = requests.get(f"{self.base_url}/report/{report_id}")
                    report_response.raise_for_status()
                    report_data = report_response.json()
                    
                    if not report_data.get("success", False):
                        logger.error(f"[MiroFishClient] Failed to fetch report content: {report_response.text}")
                        return data["data"].get("report", data["data"])
                    
                    # Extract markdown content
                    markdown_content = report_data["data"].get("markdown_content", "")
                    
                    # Save to file
                    with open("mirofish_final_report.md", "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    logger.info("[MiroFishClient] Report saved to mirofish_final_report.md")
                    
                    # Score with local LLM
                    scores = self._score_with_llm(markdown_content)
                    logger.info(f"[MiroFishClient] LLM scores: {scores}")
                    
                    # Return combined data
                    return {
                        **data["data"],
                        "llm_scores": scores
                    }
                elif status in ("failed", "error"):
                    raise RuntimeError(f"Report generation failed with status: {status}")
                else:
                    # Wait before next poll
                    if attempt < max_retries - 1:
                        time.sleep(poll_interval)

            except requests.exceptions.RequestException as e:
                logger.warning(f"[MiroFishClient] Request error during report polling: {e}")
                if attempt < max_retries - 1:
                    time.sleep(poll_interval)

        raise RuntimeError(f"Report generation polling timed out after {max_retries} attempts")
