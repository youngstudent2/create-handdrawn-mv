#version 330
in vec2 in_uv;
out vec2 uv;
uniform vec3 pos;
uniform vec2 size;
uniform vec3 rot;
uniform vec4 camera;
uniform float time;
uniform float deform;
void main(){
 uv=in_uv;
 vec2 p=(vec2(in_uv.x,1.0-in_uv.y)-.5)*size;
 float edge=pow(abs(in_uv.x-.5)*2.,2.0);
 float hair=sin(in_uv.y*6.0-time*2.4)*edge*deform;
 p.x+=hair*size.x*.025;
 p.y+=cos(in_uv.x*9.-time*2.)*edge*deform*size.y*.006;
 vec3 q=vec3(p,0.);
 float c=cos(rot.x),s=sin(rot.x);q.yz=mat2(c,s,-s,c)*q.yz;
 c=cos(rot.y);s=sin(rot.y);q.xz=mat2(c,s,-s,c)*q.xz;
 c=cos(rot.z);s=sin(rot.z);q.xy=mat2(c,s,-s,c)*q.xy;
 q+=pos;
 float perspective=18./max(2.,18.-q.z);
 q.xy=(q.xy-camera.xy)*perspective;
 c=cos(camera.z);s=sin(camera.z);q.xy=mat2(c,-s,s,c)*q.xy;
 gl_Position=vec4(q.x/7.2*camera.w,q.y/5.4*camera.w,0.,1.);
}
