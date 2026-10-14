#version 330
in vec2 vuv;out vec4 frag;
uniform float time;
uniform int mode;
uniform float energy;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
void main(){
 vec2 uv=vuv-.5;uv.x*=1.333333;
 float r=length(uv),a=atan(uv.y,uv.x);
 vec3 col=vec3(.018,.024,.047);
 if(mode==1){col=vec3(.87,.79,.69);col-=r*.13;float ray=pow(max(0.,sin(a*28.+time*.3)),34.);col-=ray*.13;}
 if(mode==2){
  float f=pow(abs(sin(a*19.+time*.36+sin(a*5.))),36.);
  vec3 rainbow=.5+.5*cos(a*3.+vec3(0.,2.1,4.2)+time*.2);
  col+=rainbow*f*(.35+energy*.3)*(1.-exp(-r*6.));
  col+=vec3(.07,.02,.06)*exp(-r*4.);
 }
 if(mode==3){
  float f=sin(uv.x*13.+time)*sin(uv.y*18.-time*.7);
  col=vec3(.012,.045,.09)+vec3(.015,.16,.22)*pow(abs(f),10.);
 }
 for(int l=0;l<3;l++){
  float s=25.+float(l)*17.;vec2 p=uv*s+vec2(time*(.12+float(l)*.06),time*.17);
  vec2 id=floor(p);vec2 q=fract(p)-.5;float h=hash(id+float(l)*83.);
  float d=length(q-(vec2(h,fract(h*37.))-.5)*.7);
  float star=pow(max(0.,1.-d*22.),2.)*step(.91,h);
  star*=.5+.5*sin(time*(2.+h*2.)+h*24.);
  if(mode!=1)col+=vec3(.7,.79,.94)*star*.85;
 }
 if(mode==4){
  float spokes=pow(max(0.,sin(a*51.+sin(a*4.)+time*.2)),36.);
  float run=pow(max(0.,sin(30.*r-time*8.)),12.);
  col+=vec3(.35,.6,.85)*spokes*run*(.2+r)*energy;
 }
 frag=vec4(col,1.);
}
