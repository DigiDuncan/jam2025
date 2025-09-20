#version 330

uniform sampler2D base;
uniform sampler2D source;
uniform sampler2D blur;
uniform float strength;

in vec2 vs_uv;

out vec4 fs_colour;

void main(){
    vec4 base_sample = texture(base, vs_uv);
    vec4 source_sample = texture(source, vs_uv);
    vec3 final_sample = base_sample.rgb * (1.0 - source_sample.a) + source_sample.rgb * source_sample.a;
    fs_colour = vec4(final_sample + texture(blur, vs_uv).rgb * strength, 1.0);
}