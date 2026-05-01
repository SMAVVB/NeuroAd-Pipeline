// Data file for NeuroAd Dashboard
// Contains all scores from the apple_vs_samsung campaign

// TRIBE v2 Scores
export const tribeScores = {
  assetPath: "campaigns/apple_vs_samsung/assets/apple_iphone17pro_ultimate.mp4",
  assetType: "video",
  neuralEngagement: 0.1809002012014389,
  emotionalImpact: 0.1551876962184906,
  faceResponse: 0.20565906167030334,
  sceneResponse: 0.17619585990905762,
  motionResponse: 0.1807614266872406,
  languageEngagement: 0.168828547000885,
  temporalPeak: 62.0,
  nSegments: 66,
  brainMapPath: "campaigns/apple_vs_samsung/scores/apple_iphone17pro_ultimate_tribe_preds.npy",
  inferenceTimeS: 6.1
};

// ViNet Saliency Scores
export const viNetScores = {
  assetPath: "campaigns/apple_vs_samsung/assets/apple_iphone17pro_ultimate.mp4",
  assetType: "video",
  productAttention: 0.0,
  brandAttention: 0.0,
  ctaAttention: 0.0,
  centerBias: 1.0,
  temporalVariance: 0.0,
  meanSaliency: 0.06020105257630348,
  saliencyMapPath: "campaigns/apple_vs_samsung/scores/apple_iphone17pro_ultimate_saliency_mean.npy",
  heatmapPngPath: "campaigns/apple_vs_samsung/scores/apple_iphone17pro_ultimate_saliency_heatmap.png",
  overlayPngPath: "campaigns/apple_vs_samsung/scores/apple_iphone17pro_ultimate_saliency_frame016.png",
  inferenceTimeS: 6.2
};

// CLIP Brand Scores
export const clipScores = {
  assetPath: "campaigns/apple_vs_samsung/assets/apple_iphone17pro_ultimate.mp4",
  brandMatchScore: 0.200009765625,
  topLabel: "cinematic storytelling",
  topLabelScore: 0.2078125,
  allScores: {
    "sleek minimalist design": 0.19326171875,
    "vibrant colorful energy": 0.19736328125,
    "cinematic storytelling": 0.2078125,
    "feature demonstration": 0.20166015625,
    "emotional lifestyle": 0.199951171875
  }
};

// MiroFish Social Scores (derived from report)
export const miroFishScores = {
  viralityScore: 0.500,
  positiveSentiment: 0.500,
  brandAffinity: 0.800,
  audienceMatch: 0.500,
  emotionalResonance: 0.500,
  shareability: 0.500,
  summary: "Brand-driven, Content-weak: Das Video nutzt die starke Apple-Brand, scheitert aber an der spezifischen kreativen Umsetzung, um aktive Interaktionen auszulösen.",
  strengths: ["Starke Markenaffinität"],
  weaknesses: ["Geringe Zielgruppenübereinstimmung", "Schwacher emotionaler Resonanz-Effekt"],
  recommendations: [
    "Machen Sie das Creative teilerfreundlicher",
    "Optimieren Sie die Zielgruppenansprache",
    "Stärken Sie den emotionalen Call-to-Action"
  ]
};

// Campaign Data
export const campaignData = {
  id: "apple_vs_samsung",
  name: "Apple vs Samsung",
  brand: "Apple",
  creativeRankings: {
    overall: [
      "campaigns/apple_vs_samsung/assets/apple_pay_outrun.mp4",
      "campaigns/apple_vs_samsung/assets/apple_iphone17_scratch.mp4",
      "campaigns/apple_vs_samsung/assets/apple_iphone17pro_ultimate.mp4"
    ],
    byModule: {
      tribe: ["campaigns/apple_vs_samsung/assets/apple_pay_outrun.mp4"],
      mirofish: ["campaigns/apple_vs_samsung/assets/apple_iphone17_scratch.mp4"],
      clip: ["campaigns/apple_vs_samsung/assets/apple_iphone17pro_ultimate.mp4"],
      vinet: ["campaigns/apple_vs_samsung/assets/apple_pay_outrun.mp4"]
    }
  },
  moduleAnalyses: {
    tribe: {
      summary: "Die vorliegenden TRIBE v2 Scores zeichnen das Bild einer hochgradig kontrollierten, minimalistischen Werbestrategie, die typisch für die Markenführung von Apple ist. Das durchschnittliche Engagement von 0,180 liegt in einem moderaten Bereich, was auf eine bewusste Vermeidung von überreizenden Stimuli hindeutet. Anstatt auf kurzfristige Schockeffekte oder aggressive visuelle Reize zu setzen, erzeugt das Video eine subtile, aber konstante neuronale Aktivierung. Besonders auffällig ist die Facial Response von 0,206, welche den höchsten Einzelwert darstellt. Neurologisch lässt dies auf eine starke Aktivierung der Fusiform Face Area schließen, wobei die Spiegelneuronen des Betrachters durch die Darstellung menschlicher Emotionen oder Interaktionen angesprochen werden. Dies schafft eine empathische Verbindung zur Marke, ohne den Nutzer kognitiv zu überfordern.\n\nDie neurologischen Mechanismen basieren hier primär auf einer tonischen Aufmerksamkeit statt auf phasischen Peaks. Während der emotionale Impact mit 0,159 eher niedrig ausfällt, deutet dies auf eine kognitive Verarbeitung hin, die auf Ästhetik und Prestige setzt statt auf primäre Affekte wie Angst oder extreme Freude. Die Motion- und Szenen-Response bewegen sich auf einem sehr ähnlichen Niveau, was eine harmonische visuelle Rhythmik belegt. Es gibt keine abrupten Brüche in der Bildsprache, die das Gehirn zu einer abrupten Neuorientierung zwingen würden.\n\nDie Engagement-Stabilität von 0,986 ist der kritischste Wert dieser Analyse. Ein Wert so nah an der Perfektion bedeutet, dass die Aufmerksamkeit über den gesamten Verlauf des Videos nahezu linear bleibt. Es treten keine signifikanten Abfälle auf, was das Risiko eines Attentional Blink minimiert. Für die Aufmerksamkeitsdauer bedeutet dies, dass der Betrachter in einen Zustand des Flows versetzt wird, in dem die Information ohne Widerstand aufgenommen wird. Die neuronale Last bleibt konstant, was eine hohe Verarbeitungsqualität der Markenbotschaft ermöglicht.\n\nDer zeitliche Peak bei Segment 31 von 36 belegt eine klassische narrative Spannungskurve. Das Engagement wird über den Großteil des Videos stabil gehalten und erst kurz vor dem Ende auf einen Höhepunkt geführt. Wissenschaftlich betrachtet handelt es sich um eine Slow-Burn-Strategie, bei der die neuronale Erregung graduell gesteigert wird, um die finale Markenbotschaft oder das Produkt-Reveal mit maximaler Wirkung zu platzieren. Die Werbewirkung ist somit nicht auf kurzfristige Aufmerksamkeit, sondern auf eine tiefe, stabile Verankerung im Langzeitgedächtnis durch konsistente ästhetische Stimulation ausgelegt.",
      strengths: [
        "Starke neurale Aktivierung (0.181)",
        "Starke Gesichts-Response (Fokus auf Menschen)",
        "Hoher emotionaler Impact",
        "Hohe Engagement-Stabilität über den gesamten Videoverlauf",
        "Starke Motion-Response (Bewegungserkennung)",
        "Starke neurale Aktivierung (0.205)",
        "Starke neurale Aktivierung (0.184)"
      ],
      weaknesses: [
        "Niedrige neurale Aktivierung (<0.18)",
        "Geringer emotionaler Impact",
        "Schwache Gesichts-Response",
        "Schwache Motion-Response"
      ],
      recommendations: [
        "Integrieren Sie mehr dynamische Bewegungselemente",
        "Erhöhen Sie den Fokus auf menschliche Gesichter im Video",
        "Stärken Sie den emotionalen Call-to-Action"
      ]
    },
    mirofish: {
      summary: "Resonanzmuster & Performance-Analyse: Massive Differenz zwischen Markenaffinität (0.800) und sozialer Resonanz (0.500). Brand-Carry-Effekt: Die hohe Markenaffinität stützt das Creative, während die eigentliche Performance (Note C) unter dem Durchschnitt (0.575) liegt. Engagement-Defizit: Zielgruppenübereinstimmung, emotionale Resonanz und Teilbarkeit stagnieren auf einem neutralen Median (0.500). Ergebnis: Das Video nutzt die starke Apple-Brand, scheitert aber an der spezifischen kreativen Umsetzung, um aktive Interaktionen auszulösen.",
      strengths: ["Starke Markenaffinität"],
      weaknesses: ["Geringe Zielgruppenübereinstimmung", "Schwacher emotionaler Resonanz-Effekt"],
      recommendations: [
        "Machen Sie das Creative teilerfreundlicher",
        "Optimieren Sie die Zielgruppenansprache",
        "Stärken Sie den emotionalen Call-to-Action"
      ]
    },
    clip: {
      summary: "Brand Match Score: 0.200 (Kategorie: weak). Kritisch niedriger Wert. Die visuelle Umsetzung korreliert kaum mit der etablierten Apple-Design-DNA. Mangelnde Minimalistik: Der niedrigste Score bei sleek minimalist design (0.193) ist fatal. Übersteigerte Farbsättigung: Vibrant colorful energy (0.197) steht im Kontrast zur typischen, kontrollierten und hochwertigen Farbpalette der Marke. Visuelle Diffusion: Die geringe Differenz zwischen den Scores (0.193 bis 0.208) deutet auf ein undefiniertes visuelles Konzept hin.",
      strengths: [
        "Klare visuelle Ausrichtung: cinematic storytelling",
        "Klare visuelle Ausrichtung: feature demonstration"
      ],
      weaknesses: [
        "Schwache Brand-Konsistenz (0.200)",
        "Geringe Label-Diskriminierung (zu viele ähnliche Scores)"
      ],
      recommendations: [
        "Schärfen Sie die visuelle Botschaft",
        "Stärken Sie die visuelle Brand Identity"
      ]
    },
    viNet: {
      summary: "Analyse der visuellen Aufmerksamkeitsführung: Saliency-Kollaps: Gesamte Aufmerksamkeitsscores bei 0.000. Keine visuelle Stimulation detektiert. Extremer Center Bias (1.00): Fokus starr auf dem Bildzentrum fixiert. Keine dynamische Blickführung über das Frame. Null-Varianz: Zeitliche Varianz von 0.000 signalisiert absolute Statik.",
      strengths: ["Konsistente Aufmerksamkeit über den Videoverlauf"],
      weaknesses: ["Niedrige Aufmerksamkeitssteuerung (0.000)", "Schwache Fokuspunkt-Qualität"],
      recommendations: [
        "Lenken Sie die Aufmerksamkeit stärker auf das Produkt",
        "Stärken Sie die Markenpräsenz visuell",
        "Machen Sie den Call-to-Action sichtbarer"
      ]
    }
  },
  masterSummary: "### Gesamtwirkung der Werbekampagne:\nDie Werbekampagne von Apple zeigt eine starke Markenidentität, aber Schwächen in visueller Konsistenz und Engagement. Während die neurale Aktivierung und emotionale Resonanz punkten, fehlt es an dynamischer visueller Aufmerksamkeitsführung und emotionaler Tiefe.\n\n### Starke Ergebnisse:\n- **TRIBE Analysis:** Hohe neurale Aktivierung, starke Gesichts-Response und emotionaler Impact.\n- **MIROFISH Analysis:** Starke Markenaffinität, die das Creative stützt.\n\n### Verbesserungspotenzial:\n- **CLIP Analysis:** Schwache Brand-Konsistenz und mangelnde Minimalistik.\n- **VINET Analysis:** Niedrige Aufmerksamkeitssteuerung und statische visuelle Elemente.\n\n### Handlungsempfehlungen:\n1. **Verbesserte visuelle Aufmerksamkeitsführung:** Dynamischere Elemente und bessere Blickführung.\n2. **Stärkere emotionale Resonanz:** Tiefergehende emotionale Momente in Inhalten.\n3. **Konsistente Markenästhetik:** Wiederherstellung der minimalistischen Apple-Design-DNA.\n4. **Optimierung der sozialen Resonanz:** Verbesserung von Engagement und Teilbarkeit.",
  recommendations: [
    "Integrieren Sie mehr dynamische Bewegungselemente in die Videos, um die visuelle Attraktivität zu erhöhen.",
    "Konzentrieren Sie sich stärker auf menschliche Gesichter, um eine emotionale Verbindung zum Publikum herzustellen.",
    "Stärken Sie den emotionalen Call-to-Action, um die Zuschauer zu einer Reaktion zu bewegen.",
    "Machen Sie das Creative teilerfreundlicher, indem Sie es ansprechend und einfach weiterzuempfehlen gestalten.",
    "Optimieren Sie die Zielgruppenansprache, um die Botschaft präziser an die Bedürfnisse der Zielgruppe anzupassen.",
    "Schärfen Sie die visuelle Botschaft, um die Kernnachricht klarer zu vermitteln.",
    "Stärken Sie die visuelle Markenidentität, um die Erkennbarkeit der Marke zu erhöhen.",
    "Lenken Sie die Aufmerksamkeit stärker auf das Produkt, um dessen Vorteile hervorzuheben.",
    "Machen Sie den Call-to-Action sichtbarer, um die Konversion zu fördern."
  ]
};

// Helper function to calculate grade from score
export const calculateGrade = (score) => {
  if (score >= 0.7) return { grade: 'A', color: '#10B981' };
  if (score >= 0.5) return { grade: 'B', color: '#3B82F6' };
  if (score >= 0.3) return { grade: 'C', color: '#F59E0B' };
  return { grade: 'D', color: '#EF4444' };
};

// Export all scores as default export
export default {
  tribeScores,
  viNetScores,
  clipScores,
  miroFishScores,
  campaignData
};
