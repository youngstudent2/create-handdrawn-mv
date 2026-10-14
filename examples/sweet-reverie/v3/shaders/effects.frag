#version 330
in vec2 vuv;out vec4 frag;
uniform sampler2D tex;
uniform float time;
uniform int effect;
uniform float amount;
uniform float zoomblur;
uniform float chroma;
uniform float bloom;
uniform float fade;
uniform float exposure;
float rnd(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
vec2 mirrorUV(vec2 p){return 1.-abs(mod(p,2.)-1.);}
vec3 sampleColor(vec2 p){return texture(tex,mirrorUV(p)).rgb;}
void main(){
 vec2 uv=vuv;vec2 p=uv-.5;
 if(effect==1){uv+=vec2(sin(uv.y*24.+time*2.1),cos(uv.x*21.-time*1.5))*.010*amount;}
 if(effect==2){
  vec2 d=p*vec2(1.3333,1.);float r=length(d),a=atan(d.y,d.x);
  a=abs(mod(a+time*.18,1.0471976)-.5235988);
  vec2 q=vec2(cos(a),sin(a))*r;uv=mix(uv,q/vec2(1.3333,1.)+.5,amount);
 }
 if(effect==3){
  vec2 q=p;float mag=max(abs(q.x),abs(q.y));
  float level=floor(log(max(mag,.001)/.48)/log(.67));
  float fac=pow(.67,max(0.,level));
  float angle=max(0.,level)*.16+time*.05*amount;
  q=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*q/fac;
  uv=mix(uv,q*.9+.5,amount);
 }
 if(effect==4){
  float row=floor(uv.y*22.);float n=rnd(vec2(row,floor(time*18.)));
  uv.x+=(n-.5)*.12*amount*step(.66,n);
 }
 if(effect==5){
  float drop=exp(-p.x*p.x*70.)*smoothstep(.48,.18,uv.y);
  uv.y+=drop*.30*amount;uv.x+=sin(uv.y*16.-time*4.)*.025*amount;
 }
 vec2 tocenter=.5-uv;vec3 col=vec3(0.);float total=0.;
 for(int i=0;i<9;i++){
  float q=(float(i)-4.)/4.;float weight=1.-abs(q)*.68;
  vec2 b=uv+tocenter*q*zoomblur;
  vec2 split=normalize(tocenter+vec2(.00001))*chroma;
  col+=vec3(sampleColor(b+split).r,sampleColor(b).g,sampleColor(b-split).b)*weight;total+=weight;
 }
 col/=total;
 if(bloom>0.){
  vec3 glow=vec3(0.);
  for(int j=0;j<8;j++){
   float a=float(j)*.785398;
   vec3 c=sampleColor(uv+vec2(cos(a),sin(a))*.009);
   glow+=max(c-.66,vec3(0.));
  }
  col+=glow*(bloom/8.);
 }
 float grain=(rnd(gl_FragCoord.xy+time*74.)-.5)*.018;
 float vignette=1.-.24*pow(length(p*vec2(1.1,1.)),1.6);
 col=(col*vignette+grain)*exposure;
 col=mix(vec3(.01,.015,.03),col,fade);
 frag=vec4(col,1.);
}
