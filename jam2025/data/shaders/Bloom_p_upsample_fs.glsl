#version 330

// https://learnopengl.com/Guest-Articles/2022/Phys.-Based-Bloom

// This shader performs upsampling on a texture,
// as taken from Call Of Duty method, presented at ACM Siggraph 2014.

// Remember to add bilinear minification filter for this texture!
// Remember to use a floating-point texture format (for HDR)!
// Remember to use edge clamping for this texture!
uniform sampler2D source;
uniform float radius;

in vec2 vs_uv;
out vec3 fs_colour;

void main(){
    float x = radius;
    float y = radius;

    // Take 9 samples around current texel:
    // a - b - c
    // d - e - f
    // g - h - i
    // === ('e' is the current texel) ===
    vec3 a = texture(source, vec2(vs_uv.x - x, vs_uv.y + y)).rgb;
    vec3 b = texture(source, vec2(vs_uv.x,     vs_uv.y + y)).rgb;
    vec3 c = texture(source, vec2(vs_uv.x + x, vs_uv.y + y)).rgb;

    vec3 d = texture(source, vec2(vs_uv.x - x, vs_uv.y)).rgb;
    vec3 e = texture(source, vec2(vs_uv.x,     vs_uv.y)).rgb;
    vec3 f = texture(source, vec2(vs_uv.x + x, vs_uv.y)).rgb;

    vec3 g = texture(source, vec2(vs_uv.x - x, vs_uv.y - y)).rgb;
    vec3 h = texture(source, vec2(vs_uv.x,     vs_uv.y - y)).rgb;
    vec3 i = texture(source, vec2(vs_uv.x + x, vs_uv.y - y)).rgb;
    
    // Apply weighted distribution, by using a 3x3 tent filter:
    //  1   | 1 2 1 |
    // -- * | 2 4 2 |
    // 16   | 1 2 1 |
    fs_colour = (e*4.0 + (b+d+f+h)*2.0 + (a+c+g+i)) / 16.0 ;
}
