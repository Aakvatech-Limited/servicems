import{L as m,o as p,c as u,b as o,i as n,d as c,j as f,M as r,B as _,N as w,r as t}from"./index.c5d94d34.js";const g={class:"m-3 flex flex-row items-center justify-center"},B=m({__name:"Login",setup(x){function l(a){let e=new FormData(a.target);r.login.submit({email:e.get("email"),password:e.get("password")})}return(a,e)=>{const s=t("Input"),i=t("Button"),d=t("Card");return p(),u("div",g,[o(d,{title:"Login to your FrappeUI App!",class:"w-full max-w-md mt-4"},{default:n(()=>[c("form",{class:"flex flex-col space-y-2 w-full",onSubmit:w(l,["prevent"])},[o(s,{required:"",name:"email",type:"text",placeholder:"johndoe@email.com",label:"User ID"}),o(s,{required:"",name:"password",type:"password",placeholder:"\u2022\u2022\u2022\u2022\u2022\u2022",label:"Password"}),o(i,{loading:f(r).login.loading,variant:"solid"},{default:n(()=>e[0]||(e[0]=[_("Login")])),_:1},8,["loading"])],32)]),_:1})])}}});export{B as default};