'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, AlertCircle, Lightbulb } from 'lucide-react'

interface AIAnalysisProps {
  summary: string
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
}

export function AIAnalysis({ summary, strengths, weaknesses, recommendations }: AIAnalysisProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-indigo flex items-center justify-center">
            <span className="text-indigo-foreground text-xs font-bold">AI</span>
          </div>
          Analysis Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-muted-foreground leading-relaxed">{summary}</p>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="space-y-3">
            <h4 className="font-medium flex items-center gap-2 text-emerald-600">
              <CheckCircle className="h-4 w-4" />
              Strengths
            </h4>
            <ul className="space-y-2">
              {strengths.map((strength, i) => (
                <li key={i} className="text-sm text-muted-foreground flex gap-2">
                  <span className="text-emerald-500 mt-1 shrink-0">+</span>
                  {strength}
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium flex items-center gap-2 text-amber-600">
              <AlertCircle className="h-4 w-4" />
              Weaknesses
            </h4>
            <ul className="space-y-2">
              {weaknesses.map((weakness, i) => (
                <li key={i} className="text-sm text-muted-foreground flex gap-2">
                  <span className="text-amber-500 mt-1 shrink-0">-</span>
                  {weakness}
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium flex items-center gap-2 text-indigo">
              <Lightbulb className="h-4 w-4" />
              Recommendations
            </h4>
            <ul className="space-y-2">
              {recommendations.map((rec, i) => (
                <li key={i} className="text-sm text-muted-foreground flex gap-2">
                  <span className="text-indigo font-mono mt-0.5 shrink-0">{i + 1}.</span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
