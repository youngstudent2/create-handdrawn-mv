#version 330
in vec2 uv;
out vec4 frag;
uniform sampler2D tex;
uniform sampler2D texB;
uniform float pose_mix;
uniform float opacity;
uniform vec3 tint;
uniform float mono;
uniform float reveal;
uniform float time;
uniform int maskmode;
void main(){
 vec4 c=texture(tex,uv);
 if(pose_mix>0.){
  vec4 b=texture(texB,uv);
  float a=mix(c.a,b.a,pose_mix);
  c=vec4(mix(c.rgb*c.a,b.rgb*b.a,pose_mix)/max(a,.0001),a);
 }
 float gray=dot(c.rgb,vec3(.299,.587,.114));
 c.rgb=mix(c.rgb,vec3(gray),mono)*tint;
 c.a*=opacity;
 if(maskmode==1){vec2 p=(uv-.5)*vec2(1.,1.2);c.a*=1.-smoothstep(.48,.50,length(p));}
 if(maskmode==2){float edge=uv.y+.035*sin(uv.x*47.)+.017*sin(uv.x*113.);c.a*=1.-smoothstep(reveal-.04,reveal+.04,edge);}
 if(maskmode==3){float d=length((uv-.5)*vec2(1.,1.2));c.a*=1.-smoothstep(reveal-.035,reveal+.035,d);}
 if(c.a<.001)discard;
 frag=c;
}
