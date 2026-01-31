"""
Neon Heart Effect
=================

WebGL-based animated neon glowing heart for Streamlit pages.
Creates a mathematically perfect heart with animated flowing segments and custom messages.

Based on the mathematical heart curve with WebGL shader rendering.
"""

from typing import Optional, List, Tuple
import streamlit as st
import random


def neon_heart(
    duration: Optional[int] = None,
    colors: Optional[List[Tuple[float, float, float]]] = None,
    message: Optional[str] = None,
    message_position: str = "center",
    message_color: str = "#FFFFFF",
    message_size: int = 48,
    intensity: float = 1.3,
    radius: float = 0.008,
    speed: float = 0.5,
    z_index: int = 999999,
    key: Optional[str] = None,
) -> None:
    """
    Display WebGL-based neon glowing heart animation with optional custom message.

    Creates a mathematically perfect animated heart using WebGL shaders with flowing
    neon glow segments. Perfect for proposals, Valentine's Day, love-themed content,
    or any celebration of love.

    Args:
        duration: Effect duration in seconds (default: None = infinite)
        colors: List of RGB tuples for glow colors (default: pink & blue)
            - Each tuple is (R, G, B) with values 0.0-1.0
            - First color: segment 1 glow
            - Second color: segment 2 glow
            - Example: [(1.0, 0.05, 0.3), (0.1, 0.4, 1.0)]
        message: Custom text message to display (default: None)
        message_position: Where to place message
            - "center": Center of viewport (default)
            - "top": Above heart
            - "bottom": Below heart
        message_color: Hex color code for message text (default: "#FFFFFF")
        message_size: Font size in pixels (default: 48)
        intensity: Glow intensity multiplier (default: 1.3, range: 0.5-3.0)
        radius: Glow radius (default: 0.008, range: 0.001-0.02)
        speed: Animation speed multiplier (default: 0.5, range: 0.1-2.0)
        z_index: CSS z-index for layering (default: 999999)
        key: Unique identifier for multiple effects

    Returns:
        None (visual effects don't return values)

    Examples:
        ```python
        import streamlit as st
        from streamlit_effects import neon_heart

        # Simple glowing heart
        st.title("💖 Valentine's Day Special")
        neon_heart()

        # With custom message
        neon_heart(
            message="I Love You",
            message_position="center",
            message_size=64,
            duration=10
        )

        # Proposal style
        if st.button("💍 Pop the Question"):
            neon_heart(
                message="Will You Marry Me?",
                colors=[
                    (1.0, 0.84, 0.0),  # Gold
                    (1.0, 1.0, 1.0),   # White
                ],
                message_position="bottom",
                message_size=72,
                duration=20,
                intensity=2.0,
                key="proposal"
            )

        # Fire theme
        neon_heart(
            message="You're Hot! 🔥",
            colors=[
                (1.0, 0.0, 0.0),   # Red
                (1.0, 0.5, 0.0),   # Orange
            ],
            speed=1.0,
            intensity=1.8
        )
        ```

    Performance Notes:
        - Requires WebGL-capable browser (most modern browsers)
        - GPU-accelerated rendering
        - Single heart recommended for optimal performance
        - Falls back gracefully if WebGL is unavailable
    """
    # Default neon colors if not provided (pink & blue)
    if colors is None:
        colors = [
            (1.0, 0.05, 0.3),  # Pink glow
            (0.1, 0.4, 1.0),  # Blue glow
        ]

    # Ensure we have exactly 2 colors
    if len(colors) < 2:
        colors = colors + [(1.0, 0.05, 0.3)] * (2 - len(colors))
    colors = colors[:2]

    # Generate unique effect ID
    effect_id = key or f"neon-heart-{random.randint(1000, 9999)}"

    # Convert speed to shader speed (negative for flow direction)
    shader_speed = -speed

    # Message positioning CSS
    if message_position == "center":
        message_css = "top: 50%; left: 50%; transform: translate(-50%, -50%);"
        animation_name = "heartbeat-message-center"
    elif message_position == "top":
        message_css = "top: 20%; left: 50%; transform: translate(-50%, 0);"
        animation_name = "heartbeat-message-top"
    else:  # bottom
        message_css = "bottom: 20%; left: 50%; transform: translate(-50%, 0);"
        animation_name = "heartbeat-message-bottom"

    # Message HTML
    message_html = ""
    if message:
        message_html = f"""
        <div class="heart-message" style="
            position: absolute;
            {message_css}
            color: {message_color};
            font-size: {message_size}px;
            font-family: 'Arial', sans-serif;
            font-weight: bold;
            text-align: center;
            text-shadow: 
                0 0 10px rgba(255, 255, 255, 0.8),
                0 0 20px rgba(255, 255, 255, 0.6),
                0 0 30px rgba(255, 255, 255, 0.4);
            pointer-events: none;
            z-index: {z_index + 1};
            white-space: nowrap;
            animation: {animation_name} 1.5s ease-in-out infinite;
        ">{message}</div>
        """

    # Complete HTML with WebGL implementation
    html = f"""
<style>
    #neon-heart-container-{effect_id} {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: {z_index};
        pointer-events: none;
        overflow: hidden;
        background-color: rgba(0, 0, 0, 0.8);
    }}
    
    #neon-heart-canvas-{effect_id} {{
        width: 100%;
        height: 100%;
        display: block;
    }}
    
    @keyframes heartbeat-message-center {{
        0%, 100% {{
            transform: translate(-50%, -50%) scale(1);
        }}
        50% {{
            transform: translate(-50%, -50%) scale(1.05);
        }}
    }}
    
    @keyframes heartbeat-message-top {{
        0%, 100% {{
            transform: translate(-50%, 0) scale(1);
        }}
        50% {{
            transform: translate(-50%, 0) scale(1.05);
        }}
    }}
    
    @keyframes heartbeat-message-bottom {{
        0%, 100% {{
            transform: translate(-50%, 0) scale(1);
        }}
        50% {{
            transform: translate(-50%, 0) scale(1.05);
        }}
    }}
</style>

<div id="neon-heart-container-{effect_id}">
    <canvas id="neon-heart-canvas-{effect_id}"></canvas>
    {message_html}
</div>

<script>
(function() {{
    var canvas = document.getElementById("neon-heart-canvas-{effect_id}");
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    // Initialize the GL context
    var gl = canvas.getContext('webgl');
    if (!gl) {{
        console.error("Unable to initialize WebGL for neon heart effect.");
        document.getElementById("neon-heart-container-{effect_id}").innerHTML = 
            '<div style="color: white; text-align: center; padding-top: 45vh;">WebGL not supported. Please use a modern browser.</div>';
        return;
    }}
    
    // Time
    var time = 0.0;
    
    // Vertex shader source
    var vertexSource = `
    attribute vec2 position;
    void main() {{
        gl_Position = vec4(position, 0.0, 1.0);
    }}
    `;
    
    // Fragment shader source with customizable colors
    var fragmentSource = `
    precision highp float;
    
    uniform float width;
    uniform float height;
    vec2 resolution = vec2(width, height);
    
    uniform float time;
    
    #define POINT_COUNT 8
    
    vec2 points[POINT_COUNT];
    const float speed = {shader_speed};
    const float len = 0.25;
    float intensity = {intensity};
    float radius = {radius};
    
    // Signed distance to a quadratic bezier
    float sdBezier(vec2 pos, vec2 A, vec2 B, vec2 C) {{    
        vec2 a = B - A;
        vec2 b = A - 2.0*B + C;
        vec2 c = a * 2.0;
        vec2 d = A - pos;
        
        float kk = 1.0 / dot(b,b);
        float kx = kk * dot(a,b);
        float ky = kk * (2.0*dot(a,a)+dot(d,b)) / 3.0;
        float kz = kk * dot(d,a);      
        
        float res = 0.0;
        
        float p = ky - kx*kx;
        float p3 = p*p*p;
        float q = kx*(2.0*kx*kx - 3.0*ky) + kz;
        float h = q*q + 4.0*p3;
        
        if(h >= 0.0) {{ 
            h = sqrt(h);
            vec2 x = (vec2(h, -h) - q) / 2.0;
            vec2 uv = sign(x)*pow(abs(x), vec2(1.0/3.0));
            float t = uv.x + uv.y - kx;
            t = clamp( t, 0.0, 1.0 );
            
            vec2 qos = d + (c + b*t)*t;
            res = length(qos);
        }} else {{
            float z = sqrt(-p);
            float v = acos( q/(p*z*2.0) ) / 3.0;
            float m = cos(v);
            float n = sin(v)*1.732050808;
            vec3 t = vec3(m + m, -n - m, n - m) * z - kx;
            t = clamp( t, 0.0, 1.0 );
            
            vec2 qos = d + (c + b*t.x)*t.x;
            float dis = dot(qos,qos);
            res = dis;
            
            qos = d + (c + b*t.y)*t.y;
            dis = dot(qos,qos);
            res = min(res,dis);
            
            qos = d + (c + b*t.z)*t.z;
            dis = dot(qos,qos);
            res = min(res,dis);
            
            res = sqrt( res );
        }}
        
        return res;
    }}
    
    // Mathematical heart curve
    vec2 getHeartPosition(float t) {{
        return vec2(16.0 * sin(t) * sin(t) * sin(t),
                    -(13.0 * cos(t) - 5.0 * cos(2.0*t)
                    - 2.0 * cos(3.0*t) - cos(4.0*t)));
    }}
    
    // Glow effect
    float getGlow(float dist, float radius, float intensity) {{
        return pow(radius/dist, intensity);
    }}
    
    float getSegment(float t, vec2 pos, float offset, float scale) {{
        for(int i = 0; i < POINT_COUNT; i++) {{
            points[i] = getHeartPosition(offset + float(i)*len + fract(speed * t) * 6.28);
        }}
        
        vec2 c = (points[0] + points[1]) / 2.0;
        vec2 c_prev;
        float dist = 10000.0;
        
        for(int i = 0; i < POINT_COUNT-1; i++) {{
            c_prev = c;
            c = (points[i] + points[i+1]) / 2.0;
            dist = min(dist, sdBezier(pos, scale * c_prev, scale * points[i], scale * c));
        }}
        return max(0.0, dist);
    }}
    
    void main() {{
        vec2 uv = gl_FragCoord.xy/resolution.xy;
        float widthHeightRatio = resolution.x/resolution.y;
        vec2 centre = vec2(0.5, 0.5);
        vec2 pos = centre - uv;
        pos.y /= widthHeightRatio;
        pos.y += 0.02;
        float scale = 0.000015 * height;
        
        float t = time;
        
        // Get first segment with custom color
        float dist = getSegment(t, pos, 0.0, scale);
        float glow = getGlow(dist, radius, intensity);
        
        vec3 col = vec3(0.0);
        
        // White core
        col += 10.0*vec3(smoothstep(0.003, 0.001, dist));
        // First color glow
        col += glow * vec3({colors[0][0]}, {colors[0][1]}, {colors[0][2]});
        
        // Get second segment with custom color
        dist = getSegment(t, pos, 3.4, scale);
        glow = getGlow(dist, radius, intensity);
        
        // White core
        col += 10.0*vec3(smoothstep(0.003, 0.001, dist));
        // Second color glow
        col += glow * vec3({colors[1][0]}, {colors[1][1]}, {colors[1][2]});
        
        // Tone mapping
        col = 1.0 - exp(-col);
        
        // Gamma correction
        col = pow(col, vec3(0.4545));
        
        gl_FragColor = vec4(col, 1.0);
    }}
    `;
    
    // Window resize handler
    window.addEventListener('resize', onWindowResize, false);
    
    function onWindowResize() {{
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.uniform1f(widthHandle, window.innerWidth);
        gl.uniform1f(heightHandle, window.innerHeight);
    }}
    
    // Compile shader
    function compileShader(shaderSource, shaderType) {{
        var shader = gl.createShader(shaderType);
        gl.shaderSource(shader, shaderSource);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {{
            throw "Shader compile failed with: " + gl.getShaderInfoLog(shader);
        }}
        return shader;
    }}
    
    // Get attribute location
    function getAttribLocation(program, name) {{
        var attributeLocation = gl.getAttribLocation(program, name);
        if (attributeLocation === -1) {{
            throw 'Cannot find attribute ' + name + '.';
        }}
        return attributeLocation;
    }}
    
    // Get uniform location
    function getUniformLocation(program, name) {{
        var attributeLocation = gl.getUniformLocation(program, name);
        if (attributeLocation === -1) {{
            throw 'Cannot find uniform ' + name + '.';
        }}
        return attributeLocation;
    }}
    
    // Create shaders
    var vertexShader = compileShader(vertexSource, gl.VERTEX_SHADER);
    var fragmentShader = compileShader(fragmentSource, gl.FRAGMENT_SHADER);
    
    // Create program
    var program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    
    gl.useProgram(program);
    
    // Set up rectangle covering entire canvas
    var vertexData = new Float32Array([
        -1.0,  1.0,  // top left
        -1.0, -1.0,  // bottom left
         1.0,  1.0,  // top right
         1.0, -1.0,  // bottom right
    ]);
    
    // Create vertex buffer
    var vertexDataBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexDataBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertexData, gl.STATIC_DRAW);
    
    // Layout of data in vertex buffer
    var positionHandle = getAttribLocation(program, 'position');
    
    gl.enableVertexAttribArray(positionHandle);
    gl.vertexAttribPointer(
        positionHandle,
        2,
        gl.FLOAT,
        false,
        2 * 4,
        0
    );
    
    // Set uniform handles
    var timeHandle = getUniformLocation(program, 'time');
    var widthHandle = getUniformLocation(program, 'width');
    var heightHandle = getUniformLocation(program, 'height');
    
    gl.uniform1f(widthHandle, window.innerWidth);
    gl.uniform1f(heightHandle, window.innerHeight);
    
    var lastFrame = Date.now();
    var thisFrame;
    var animationId;
    
    function draw() {{
        // Update time
        thisFrame = Date.now();
        time += (thisFrame - lastFrame) / 1000;
        lastFrame = thisFrame;
        
        // Send uniforms to program
        gl.uniform1f(timeHandle, time);
        
        // Draw
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        
        animationId = requestAnimationFrame(draw);
    }}
    
    draw();
    
    // Auto-removal if duration specified
    {f"setTimeout(function() {{ cancelAnimationFrame(animationId); var element = document.getElementById('neon-heart-container-{effect_id}'); if (element) {{ element.remove(); }} }}, {duration * 1000});" if duration else ""}
}})();
</script>
"""

    # Inject into Streamlit
    st.html(html)
