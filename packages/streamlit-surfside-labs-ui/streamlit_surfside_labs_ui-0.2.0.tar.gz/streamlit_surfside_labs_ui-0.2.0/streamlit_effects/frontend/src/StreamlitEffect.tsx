import React, { useEffect } from "react"
import { Streamlit, withStreamlitConnection, ComponentProps } from "streamlit-component-lib"

import SnowEffect from "./components/SnowEffect"
import ConfettiEffect from "./components/ConfettiEffect"
import FireworksEffect from "./components/FireworksEffect"
import HeartsEffect from "./components/HeartsEffect"
import MatrixEffect from "./components/MatrixEffect"

const StreamlitEffect: React.FC<ComponentProps> = ({ args }) => {
  console.log("[StreamlitEffect] Component mounting")
  console.log("[StreamlitEffect] args:", args)

  useEffect(() => {
    // Notify Streamlit that component is ready
    Streamlit.setComponentReady()
    
    // Wait a moment for canvas to be sized, then auto-detect height
    const timer = setTimeout(() => {
      console.log("[StreamlitEffect] Setting auto-detected frame height")
      Streamlit.setFrameHeight()
    }, 100)
    
    return () => clearTimeout(timer)
  }, [])

  if (!args || !args.effect_type) {
    console.log("[StreamlitEffect] No args or effect_type, returning null")
    return null
  }

  console.log("[StreamlitEffect] Rendering effect type:", args.effect_type)

  // Route to appropriate effect component based on effect_type
  switch (args.effect_type) {
    case "snow":
      console.log("[StreamlitEffect] Rendering SnowEffect")
      return <SnowEffect {...args} />
    case "confetti":
      console.log("[StreamlitEffect] Rendering ConfettiEffect")
      return <ConfettiEffect {...args} />
    case "fireworks":
      console.log("[StreamlitEffect] Rendering FireworksEffect")
      return <FireworksEffect {...args} />
    case "hearts":
      console.log("[StreamlitEffect] Rendering HeartsEffect")
      return <HeartsEffect {...args} />
    case "matrix":
      console.log("[StreamlitEffect] Rendering MatrixEffect")
      return <MatrixEffect {...args} />
    default:
      console.warn(`Unknown effect type: ${args.effect_type}`)
      return null
  }
}

export default withStreamlitConnection(StreamlitEffect)
