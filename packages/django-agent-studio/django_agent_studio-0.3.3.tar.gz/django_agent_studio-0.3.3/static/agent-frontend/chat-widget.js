var ChatWidgetModule=(()=>{var Se=Object.defineProperty;var Ht=Object.getOwnPropertyDescriptor;var Ot=Object.getOwnPropertyNames;var Nt=Object.prototype.hasOwnProperty;var Lt=(e,t)=>{for(var n in t)Se(e,n,{get:t[n],enumerable:!0})},Ut=(e,t,n,s)=>{if(t&&typeof t=="object"||typeof t=="function")for(let a of Ot(t))!Nt.call(e,a)&&a!==n&&Se(e,a,{get:()=>t[a],enumerable:!(s=Ht(t,a))||s.enumerable});return e};var Wt=e=>Ut(Se({},"__esModule",{value:!0}),e);var yn={};Lt(yn,{ChatWidget:()=>Ce,default:()=>gn});var _e,H,ze,Kt,ee,We,Je,Ve,qe,Ee,Te,Me,Bt,oe={},Ge=[],jt=/acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i,pe=Array.isArray;function Q(e,t){for(var n in t)e[n]=t[n];return e}function Ie(e){e&&e.parentNode&&e.parentNode.removeChild(e)}function fe(e,t,n){var s,a,o,l={};for(o in t)o=="key"?s=t[o]:o=="ref"?a=t[o]:l[o]=t[o];if(arguments.length>2&&(l.children=arguments.length>3?_e.call(arguments,2):n),typeof e=="function"&&e.defaultProps!=null)for(o in e.defaultProps)l[o]===void 0&&(l[o]=e.defaultProps[o]);return ue(e,l,s,a,null)}function ue(e,t,n,s,a){var o={type:e,props:t,key:n,ref:s,__k:null,__:null,__b:0,__e:null,__c:null,constructor:void 0,__v:a??++ze,__i:-1,__u:0};return a==null&&H.vnode!=null&&H.vnode(o),o}function he(e){return e.children}function se(e,t){this.props=e,this.context=t}function ne(e,t){if(t==null)return e.__?ne(e.__,e.__i+1):null;for(var n;t<e.__k.length;t++)if((n=e.__k[t])!=null&&n.__e!=null)return n.__e;return typeof e.type=="function"?ne(e):null}function Xe(e){var t,n;if((e=e.__)!=null&&e.__c!=null){for(e.__e=e.__c.base=null,t=0;t<e.__k.length;t++)if((n=e.__k[t])!=null&&n.__e!=null){e.__e=e.__c.base=n.__e;break}return Xe(e)}}function Ke(e){(!e.__d&&(e.__d=!0)&&ee.push(e)&&!de.__r++||We!=H.debounceRendering)&&((We=H.debounceRendering)||Je)(de)}function de(){for(var e,t,n,s,a,o,l,c=1;ee.length;)ee.length>c&&ee.sort(Ve),e=ee.shift(),c=ee.length,e.__d&&(n=void 0,s=void 0,a=(s=(t=e).__v).__e,o=[],l=[],t.__P&&((n=Q({},s)).__v=s.__v+1,H.vnode&&H.vnode(n),Ae(t.__P,n,s,t.__n,t.__P.namespaceURI,32&s.__u?[a]:null,o,a??ne(s),!!(32&s.__u),l),n.__v=s.__v,n.__.__k[n.__i]=n,Ye(o,n,l),s.__e=s.__=null,n.__e!=a&&Xe(n)));de.__r=0}function Qe(e,t,n,s,a,o,l,c,u,i,d){var r,_,p,k,w,y,g,$=s&&s.__k||Ge,I=t.length;for(u=zt(n,t,$,u,I),r=0;r<I;r++)(p=n.__k[r])!=null&&(_=p.__i==-1?oe:$[p.__i]||oe,p.__i=r,y=Ae(e,p,_,a,o,l,c,u,i,d),k=p.__e,p.ref&&_.ref!=p.ref&&(_.ref&&De(_.ref,null,p),d.push(p.ref,p.__c||k,p)),w==null&&k!=null&&(w=k),(g=!!(4&p.__u))||_.__k===p.__k?u=Ze(p,u,e,g):typeof p.type=="function"&&y!==void 0?u=y:k&&(u=k.nextSibling),p.__u&=-7);return n.__e=w,u}function zt(e,t,n,s,a){var o,l,c,u,i,d=n.length,r=d,_=0;for(e.__k=new Array(a),o=0;o<a;o++)(l=t[o])!=null&&typeof l!="boolean"&&typeof l!="function"?(typeof l=="string"||typeof l=="number"||typeof l=="bigint"||l.constructor==String?l=e.__k[o]=ue(null,l,null,null,null):pe(l)?l=e.__k[o]=ue(he,{children:l},null,null,null):l.constructor===void 0&&l.__b>0?l=e.__k[o]=ue(l.type,l.props,l.key,l.ref?l.ref:null,l.__v):e.__k[o]=l,u=o+_,l.__=e,l.__b=e.__b+1,c=null,(i=l.__i=Jt(l,n,u,r))!=-1&&(r--,(c=n[i])&&(c.__u|=2)),c==null||c.__v==null?(i==-1&&(a>d?_--:a<d&&_++),typeof l.type!="function"&&(l.__u|=4)):i!=u&&(i==u-1?_--:i==u+1?_++:(i>u?_--:_++,l.__u|=4))):e.__k[o]=null;if(r)for(o=0;o<d;o++)(c=n[o])!=null&&!(2&c.__u)&&(c.__e==s&&(s=ne(c)),tt(c,c));return s}function Ze(e,t,n,s){var a,o;if(typeof e.type=="function"){for(a=e.__k,o=0;a&&o<a.length;o++)a[o]&&(a[o].__=e,t=Ze(a[o],t,n,s));return t}e.__e!=t&&(s&&(t&&e.type&&!t.parentNode&&(t=ne(e)),n.insertBefore(e.__e,t||null)),t=e.__e);do t=t&&t.nextSibling;while(t!=null&&t.nodeType==8);return t}function Jt(e,t,n,s){var a,o,l,c=e.key,u=e.type,i=t[n],d=i!=null&&(2&i.__u)==0;if(i===null&&c==null||d&&c==i.key&&u==i.type)return n;if(s>(d?1:0)){for(a=n-1,o=n+1;a>=0||o<t.length;)if((i=t[l=a>=0?a--:o++])!=null&&!(2&i.__u)&&c==i.key&&u==i.type)return l}return-1}function Be(e,t,n){t[0]=="-"?e.setProperty(t,n??""):e[t]=n==null?"":typeof n!="number"||jt.test(t)?n:n+"px"}function ce(e,t,n,s,a){var o,l;e:if(t=="style")if(typeof n=="string")e.style.cssText=n;else{if(typeof s=="string"&&(e.style.cssText=s=""),s)for(t in s)n&&t in n||Be(e.style,t,"");if(n)for(t in n)s&&n[t]==s[t]||Be(e.style,t,n[t])}else if(t[0]=="o"&&t[1]=="n")o=t!=(t=t.replace(qe,"$1")),l=t.toLowerCase(),t=l in e||t=="onFocusOut"||t=="onFocusIn"?l.slice(2):t.slice(2),e.l||(e.l={}),e.l[t+o]=n,n?s?n.u=s.u:(n.u=Ee,e.addEventListener(t,o?Me:Te,o)):e.removeEventListener(t,o?Me:Te,o);else{if(a=="http://www.w3.org/2000/svg")t=t.replace(/xlink(H|:h)/,"h").replace(/sName$/,"s");else if(t!="width"&&t!="height"&&t!="href"&&t!="list"&&t!="form"&&t!="tabIndex"&&t!="download"&&t!="rowSpan"&&t!="colSpan"&&t!="role"&&t!="popover"&&t in e)try{e[t]=n??"";break e}catch{}typeof n=="function"||(n==null||n===!1&&t[4]!="-"?e.removeAttribute(t):e.setAttribute(t,t=="popover"&&n==1?"":n))}}function je(e){return function(t){if(this.l){var n=this.l[t.type+e];if(t.t==null)t.t=Ee++;else if(t.t<n.u)return;return n(H.event?H.event(t):t)}}}function Ae(e,t,n,s,a,o,l,c,u,i){var d,r,_,p,k,w,y,g,$,I,N,J,z,V,K,B,q,O=t.type;if(t.constructor!==void 0)return null;128&n.__u&&(u=!!(32&n.__u),o=[c=t.__e=n.__e]),(d=H.__b)&&d(t);e:if(typeof O=="function")try{if(g=t.props,$="prototype"in O&&O.prototype.render,I=(d=O.contextType)&&s[d.__c],N=d?I?I.props.value:d.__:s,n.__c?y=(r=t.__c=n.__c).__=r.__E:($?t.__c=r=new O(g,N):(t.__c=r=new se(g,N),r.constructor=O,r.render=qt),I&&I.sub(r),r.state||(r.state={}),r.__n=s,_=r.__d=!0,r.__h=[],r._sb=[]),$&&r.__s==null&&(r.__s=r.state),$&&O.getDerivedStateFromProps!=null&&(r.__s==r.state&&(r.__s=Q({},r.__s)),Q(r.__s,O.getDerivedStateFromProps(g,r.__s))),p=r.props,k=r.state,r.__v=t,_)$&&O.getDerivedStateFromProps==null&&r.componentWillMount!=null&&r.componentWillMount(),$&&r.componentDidMount!=null&&r.__h.push(r.componentDidMount);else{if($&&O.getDerivedStateFromProps==null&&g!==p&&r.componentWillReceiveProps!=null&&r.componentWillReceiveProps(g,N),t.__v==n.__v||!r.__e&&r.shouldComponentUpdate!=null&&r.shouldComponentUpdate(g,r.__s,N)===!1){for(t.__v!=n.__v&&(r.props=g,r.state=r.__s,r.__d=!1),t.__e=n.__e,t.__k=n.__k,t.__k.some(function(f){f&&(f.__=t)}),J=0;J<r._sb.length;J++)r.__h.push(r._sb[J]);r._sb=[],r.__h.length&&l.push(r);break e}r.componentWillUpdate!=null&&r.componentWillUpdate(g,r.__s,N),$&&r.componentDidUpdate!=null&&r.__h.push(function(){r.componentDidUpdate(p,k,w)})}if(r.context=N,r.props=g,r.__P=e,r.__e=!1,z=H.__r,V=0,$){for(r.state=r.__s,r.__d=!1,z&&z(t),d=r.render(r.props,r.state,r.context),K=0;K<r._sb.length;K++)r.__h.push(r._sb[K]);r._sb=[]}else do r.__d=!1,z&&z(t),d=r.render(r.props,r.state,r.context),r.state=r.__s;while(r.__d&&++V<25);r.state=r.__s,r.getChildContext!=null&&(s=Q(Q({},s),r.getChildContext())),$&&!_&&r.getSnapshotBeforeUpdate!=null&&(w=r.getSnapshotBeforeUpdate(p,k)),B=d,d!=null&&d.type===he&&d.key==null&&(B=et(d.props.children)),c=Qe(e,pe(B)?B:[B],t,n,s,a,o,l,c,u,i),r.base=t.__e,t.__u&=-161,r.__h.length&&l.push(r),y&&(r.__E=r.__=null)}catch(f){if(t.__v=null,u||o!=null)if(f.then){for(t.__u|=u?160:128;c&&c.nodeType==8&&c.nextSibling;)c=c.nextSibling;o[o.indexOf(c)]=null,t.__e=c}else{for(q=o.length;q--;)Ie(o[q]);xe(t)}else t.__e=n.__e,t.__k=n.__k,f.then||xe(t);H.__e(f,t,n)}else o==null&&t.__v==n.__v?(t.__k=n.__k,t.__e=n.__e):c=t.__e=Vt(n.__e,t,n,s,a,o,l,u,i);return(d=H.diffed)&&d(t),128&t.__u?void 0:c}function xe(e){e&&e.__c&&(e.__c.__e=!0),e&&e.__k&&e.__k.forEach(xe)}function Ye(e,t,n){for(var s=0;s<n.length;s++)De(n[s],n[++s],n[++s]);H.__c&&H.__c(t,e),e.some(function(a){try{e=a.__h,a.__h=[],e.some(function(o){o.call(a)})}catch(o){H.__e(o,a.__v)}})}function et(e){return typeof e!="object"||e==null||e.__b&&e.__b>0?e:pe(e)?e.map(et):Q({},e)}function Vt(e,t,n,s,a,o,l,c,u){var i,d,r,_,p,k,w,y=n.props||oe,g=t.props,$=t.type;if($=="svg"?a="http://www.w3.org/2000/svg":$=="math"?a="http://www.w3.org/1998/Math/MathML":a||(a="http://www.w3.org/1999/xhtml"),o!=null){for(i=0;i<o.length;i++)if((p=o[i])&&"setAttribute"in p==!!$&&($?p.localName==$:p.nodeType==3)){e=p,o[i]=null;break}}if(e==null){if($==null)return document.createTextNode(g);e=document.createElementNS(a,$,g.is&&g),c&&(H.__m&&H.__m(t,o),c=!1),o=null}if($==null)y===g||c&&e.data==g||(e.data=g);else{if(o=o&&_e.call(e.childNodes),!c&&o!=null)for(y={},i=0;i<e.attributes.length;i++)y[(p=e.attributes[i]).name]=p.value;for(i in y)if(p=y[i],i!="children"){if(i=="dangerouslySetInnerHTML")r=p;else if(!(i in g)){if(i=="value"&&"defaultValue"in g||i=="checked"&&"defaultChecked"in g)continue;ce(e,i,null,p,a)}}for(i in g)p=g[i],i=="children"?_=p:i=="dangerouslySetInnerHTML"?d=p:i=="value"?k=p:i=="checked"?w=p:c&&typeof p!="function"||y[i]===p||ce(e,i,p,y[i],a);if(d)c||r&&(d.__html==r.__html||d.__html==e.innerHTML)||(e.innerHTML=d.__html),t.__k=[];else if(r&&(e.innerHTML=""),Qe(t.type=="template"?e.content:e,pe(_)?_:[_],t,n,s,$=="foreignObject"?"http://www.w3.org/1999/xhtml":a,o,l,o?o[0]:n.__k&&ne(n,0),c,u),o!=null)for(i=o.length;i--;)Ie(o[i]);c||(i="value",$=="progress"&&k==null?e.removeAttribute("value"):k!=null&&(k!==e[i]||$=="progress"&&!k||$=="option"&&k!=y[i])&&ce(e,i,k,y[i],a),i="checked",w!=null&&w!=e[i]&&ce(e,i,w,y[i],a))}return e}function De(e,t,n){try{if(typeof e=="function"){var s=typeof e.__u=="function";s&&e.__u(),s&&t==null||(e.__u=e(t))}else e.current=t}catch(a){H.__e(a,n)}}function tt(e,t,n){var s,a;if(H.unmount&&H.unmount(e),(s=e.ref)&&(s.current&&s.current!=e.__e||De(s,null,t)),(s=e.__c)!=null){if(s.componentWillUnmount)try{s.componentWillUnmount()}catch(o){H.__e(o,t)}s.base=s.__P=null}if(s=e.__k)for(a=0;a<s.length;a++)s[a]&&tt(s[a],t,n||typeof e.type!="function");n||Ie(e.__e),e.__c=e.__=e.__e=void 0}function qt(e,t,n){return this.constructor(e,n)}function me(e,t,n){var s,a,o,l;t==document&&(t=document.documentElement),H.__&&H.__(e,t),a=(s=typeof n=="function")?null:n&&n.__k||t.__k,o=[],l=[],Ae(t,e=(!s&&n||t).__k=fe(he,null,[e]),a||oe,oe,t.namespaceURI,!s&&n?[n]:a?null:t.firstChild?_e.call(t.childNodes):null,o,!s&&n?n:a?a.__e:t.firstChild,s,l),Ye(o,e,l)}_e=Ge.slice,H={__e:function(e,t,n,s){for(var a,o,l;t=t.__;)if((a=t.__c)&&!a.__)try{if((o=a.constructor)&&o.getDerivedStateFromError!=null&&(a.setState(o.getDerivedStateFromError(e)),l=a.__d),a.componentDidCatch!=null&&(a.componentDidCatch(e,s||{}),l=a.__d),l)return a.__E=a}catch(c){e=c}throw e}},ze=0,Kt=function(e){return e!=null&&e.constructor===void 0},se.prototype.setState=function(e,t){var n;n=this.__s!=null&&this.__s!=this.state?this.__s:this.__s=Q({},this.state),typeof e=="function"&&(e=e(Q({},n),this.props)),e&&Q(n,e),e!=null&&this.__v&&(t&&this._sb.push(t),Ke(this))},se.prototype.forceUpdate=function(e){this.__v&&(this.__e=!0,e&&this.__h.push(e),Ke(this))},se.prototype.render=he,ee=[],Je=typeof Promise=="function"?Promise.prototype.then.bind(Promise.resolve()):setTimeout,Ve=function(e,t){return e.__v.__b-t.__v.__b},de.__r=0,qe=/(PointerCapture)$|Capture$/i,Ee=0,Te=je(!1),Me=je(!0),Bt=0;var st=function(e,t,n,s){var a;t[0]=0;for(var o=1;o<t.length;o++){var l=t[o++],c=t[o]?(t[0]|=l?1:2,n[t[o++]]):t[++o];l===3?s[0]=c:l===4?s[1]=Object.assign(s[1]||{},c):l===5?(s[1]=s[1]||{})[t[++o]]=c:l===6?s[1][t[++o]]+=c+"":l?(a=e.apply(c,st(e,c,n,["",null])),s.push(a),c[0]?t[0]|=2:(t[o-2]=0,t[o]=a)):s.push(c)}return s},nt=new Map;function ot(e){var t=nt.get(this);return t||(t=new Map,nt.set(this,t)),(t=st(this,t.get(e)||(t.set(e,t=function(n){for(var s,a,o=1,l="",c="",u=[0],i=function(_){o===1&&(_||(l=l.replace(/^\s*\n\s*|\s*\n\s*$/g,"")))?u.push(0,_,l):o===3&&(_||l)?(u.push(3,_,l),o=2):o===2&&l==="..."&&_?u.push(4,_,0):o===2&&l&&!_?u.push(5,0,!0,l):o>=5&&((l||!_&&o===5)&&(u.push(o,0,l,a),o=6),_&&(u.push(o,_,0,a),o=6)),l=""},d=0;d<n.length;d++){d&&(o===1&&i(),i(d));for(var r=0;r<n[d].length;r++)s=n[d][r],o===1?s==="<"?(i(),u=[u],o=3):l+=s:o===4?l==="--"&&s===">"?(o=1,l=""):l=s+l[0]:c?s===c?c="":l+=s:s==='"'||s==="'"?c=s:s===">"?(i(),o=1):o&&(s==="="?(o=5,a=l,l=""):s==="/"&&(o<5||n[d][r+1]===">")?(i(),o===3&&(u=u[0]),o=u,(u=u[0]).push(2,0,o),o=0):s===" "||s==="	"||s===`
`||s==="\r"?(i(),o=2):l+=s),o===3&&l==="!--"&&(o=4,u=u[0])}return i(),u}(e)),t),arguments,[])).length>1?t:t[0]}var h=ot.bind(fe);var ae,L,Re,at,re=0,pt=[],U=H,rt=U.__b,it=U.__r,lt=U.diffed,ct=U.__c,ut=U.unmount,dt=U.__;function Fe(e,t){U.__h&&U.__h(L,e,re||t),re=0;var n=L.__H||(L.__H={__:[],__h:[]});return e>=n.__.length&&n.__.push({}),n.__[e]}function C(e){return re=1,Gt(ht,e)}function Gt(e,t,n){var s=Fe(ae++,2);if(s.t=e,!s.__c&&(s.__=[n?n(t):ht(void 0,t),function(c){var u=s.__N?s.__N[0]:s.__[0],i=s.t(u,c);u!==i&&(s.__N=[i,s.__[1]],s.__c.setState({}))}],s.__c=L,!L.__f)){var a=function(c,u,i){if(!s.__c.__H)return!0;var d=s.__c.__H.__.filter(function(_){return!!_.__c});if(d.every(function(_){return!_.__N}))return!o||o.call(this,c,u,i);var r=s.__c.props!==c;return d.forEach(function(_){if(_.__N){var p=_.__[0];_.__=_.__N,_.__N=void 0,p!==_.__[0]&&(r=!0)}}),o&&o.call(this,c,u,i)||r};L.__f=!0;var o=L.shouldComponentUpdate,l=L.componentWillUpdate;L.componentWillUpdate=function(c,u,i){if(this.__e){var d=o;o=void 0,a(c,u,i),o=d}l&&l.call(this,c,u,i)},L.shouldComponentUpdate=a}return s.__N||s.__}function W(e,t){var n=Fe(ae++,3);!U.__s&&ft(n.__H,t)&&(n.__=e,n.u=t,L.__H.__h.push(n))}function G(e){return re=5,ie(function(){return{current:e}},[])}function ie(e,t){var n=Fe(ae++,7);return ft(n.__H,t)&&(n.__=e(),n.__H=t,n.__h=e),n.__}function A(e,t){return re=8,ie(function(){return e},t)}function Xt(){for(var e;e=pt.shift();)if(e.__P&&e.__H)try{e.__H.__h.forEach(ge),e.__H.__h.forEach(Pe),e.__H.__h=[]}catch(t){e.__H.__h=[],U.__e(t,e.__v)}}U.__b=function(e){L=null,rt&&rt(e)},U.__=function(e,t){e&&t.__k&&t.__k.__m&&(e.__m=t.__k.__m),dt&&dt(e,t)},U.__r=function(e){it&&it(e),ae=0;var t=(L=e.__c).__H;t&&(Re===L?(t.__h=[],L.__h=[],t.__.forEach(function(n){n.__N&&(n.__=n.__N),n.u=n.__N=void 0})):(t.__h.forEach(ge),t.__h.forEach(Pe),t.__h=[],ae=0)),Re=L},U.diffed=function(e){lt&&lt(e);var t=e.__c;t&&t.__H&&(t.__H.__h.length&&(pt.push(t)!==1&&at===U.requestAnimationFrame||((at=U.requestAnimationFrame)||Qt)(Xt)),t.__H.__.forEach(function(n){n.u&&(n.__H=n.u),n.u=void 0})),Re=L=null},U.__c=function(e,t){t.some(function(n){try{n.__h.forEach(ge),n.__h=n.__h.filter(function(s){return!s.__||Pe(s)})}catch(s){t.some(function(a){a.__h&&(a.__h=[])}),t=[],U.__e(s,n.__v)}}),ct&&ct(e,t)},U.unmount=function(e){ut&&ut(e);var t,n=e.__c;n&&n.__H&&(n.__H.__.forEach(function(s){try{ge(s)}catch(a){t=a}}),n.__H=void 0,t&&U.__e(t,n.__v))};var _t=typeof requestAnimationFrame=="function";function Qt(e){var t,n=function(){clearTimeout(s),_t&&cancelAnimationFrame(t),setTimeout(e)},s=setTimeout(n,35);_t&&(t=requestAnimationFrame(n))}function ge(e){var t=L,n=e.__c;typeof n=="function"&&(e.__c=void 0,n()),L=t}function Pe(e){var t=L;e.__c=e.__(),L=t}function ft(e,t){return!e||e.length!==t.length||t.some(function(n,s){return n!==e[s]})}function ht(e,t){return typeof t=="function"?t(e):t}function Zt(e){return e.replace(/_([a-z])/g,(t,n)=>n.toUpperCase())}function He(e){return e.replace(/[A-Z]/g,t=>`_${t.toLowerCase()}`)}function ye(e){return Array.isArray(e)?e.map(ye):e!==null&&typeof e=="object"?Object.fromEntries(Object.entries(e).map(([t,n])=>[Zt(t),ye(n)])):e}function ve(e){return Array.isArray(e)?e.map(ve):e!==null&&typeof e=="object"?Object.fromEntries(Object.entries(e).map(([t,n])=>[He(t),ve(n)])):e}function we(){return"msg-"+Date.now()+"-"+Math.random().toString(36).substr(2,9)}function j(e){let t=document.createElement("div");return t.textContent=e,t.innerHTML}function mt(e){if(!e)return"";try{let t=new Date(e),s=new Date-t,a=Math.floor(s/6e4),o=Math.floor(s/36e5),l=Math.floor(s/864e5);return a<1?"Just now":a<60?`${a}m ago`:o<24?`${o}h ago`:l<7?`${l}d ago`:t.toLocaleDateString()}catch{return""}}function gt(e,t=null){if(t)return t(e);let n=j(e);return n=n.replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>"),n=n.replace(/__(.+?)__/g,"<strong>$1</strong>"),n=n.replace(/\*(.+?)\*/g,"<em>$1</em>"),n=n.replace(/_(.+?)_/g,"<em>$1</em>"),n=n.replace(/`(.+?)`/g,"<code>$1</code>"),n=n.replace(/\[(.+?)\]\((.+?)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'),n=n.replace(/\n/g,"<br>"),n}function yt(e=""){let t=n=>e?`${n}_${e}`:n;return{get(n){try{return localStorage.getItem(t(n))}catch{return null}},set(n,s){try{let a=t(n);s===null?localStorage.removeItem(a):localStorage.setItem(a,s)}catch{}}}}function vt(e="csrftoken"){let t=document.cookie.split(";");for(let s of t){let[a,o]=s.trim().split("=");if(a===e)return decodeURIComponent(o)}let n=document.querySelector('meta[name="csrf-token"]');return n?n.getAttribute("content"):null}function $e(e){if(e===0)return"0 B";let t=1024,n=["B","KB","MB","GB"],s=Math.floor(Math.log(e)/Math.log(t));return parseFloat((e/Math.pow(t,s)).toFixed(1))+" "+n[s]}function ke(e){return e?e.startsWith("image/")?"\u{1F5BC}\uFE0F":e.startsWith("video/")?"\u{1F3AC}":e.startsWith("audio/")?"\u{1F3B5}":e.includes("pdf")?"\u{1F4D5}":e.includes("spreadsheet")||e.includes("excel")?"\u{1F4CA}":e.includes("document")||e.includes("word")?"\u{1F4DD}":e.includes("presentation")||e.includes("powerpoint")?"\u{1F4FD}\uFE0F":e.includes("zip")||e.includes("compressed")?"\u{1F5DC}\uFE0F":(e.includes("text/"),"\u{1F4C4}"):"\u{1F4C4}"}function wt({config:e,debugMode:t,isExpanded:n,isSpeaking:s,messagesCount:a,isLoading:o,currentAgent:l,onClose:c,onToggleExpand:u,onToggleDebug:i,onToggleTTS:d,onClear:r,onToggleSidebar:_}){let{title:p,primaryColor:k,embedded:w,showConversationSidebar:y,showClearButton:g,showDebugButton:$,enableDebugMode:I,showTTSButton:N,showExpandButton:J,enableTTS:z,elevenLabsApiKey:V,ttsProxyUrl:K}=e,B=V||K;return h`
    <div class="cw-header" style=${{backgroundColor:k}}>
      ${y&&h`
        <button
          class="cw-header-btn cw-hamburger"
          onClick=${_}
          title="Conversations"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
      `}

      <div class="cw-title-container">
        <span class="cw-title">${j(p)}</span>
        ${l&&h`
          <span class="cw-current-agent" title="Currently active agent">
            <span class="cw-agent-indicator">🤖</span>
            <span class="cw-agent-name">${j(l.name||l.key)}</span>
          </span>
        `}
      </div>
      
      <div class="cw-header-actions">
        ${g&&h`
          <button 
            class="cw-header-btn" 
            onClick=${r}
            title="Clear"
            disabled=${o||a===0}
          >🗑️</button>
        `}
        
        ${$&&I&&h`
          <button 
            class="cw-header-btn ${t?"cw-btn-active":""}" 
            onClick=${i}
            title="Debug"
          >🐛</button>
        `}
        
        ${N&&B&&h`
          <button 
            class="cw-header-btn ${z?"cw-btn-active":""}" 
            onClick=${d}
            title="TTS"
          >${z?"\u{1F50A}":"\u{1F507}"}</button>
        `}
        
        ${J&&!w&&h`
          <button 
            class="cw-header-btn" 
            onClick=${u}
            title=${n?"Minimize":"Expand"}
          >${n?"\u2296":"\u2295"}</button>
        `}
        
        ${!w&&h`
          <button 
            class="cw-header-btn" 
            onClick=${c}
            title="Close"
          >✕</button>
        `}
      </div>
    </div>
  `}function Oe({msg:e,show:t,onToggle:n}){return t?h`
    <div class="cw-debug-payload">
      <button class="cw-debug-payload-close" onClick=${n}>×</button>
      <pre class="cw-debug-payload-content">${JSON.stringify(e,null,2)}</pre>
    </div>
  `:h`
      <button
        class="cw-debug-payload-btn"
        onClick=${n}
        title="Show message payload"
      >{ }</button>
    `}function $t({onEdit:e,onRetry:t,isLoading:n,position:s,showEdit:a=!0}){return n?null:h`
    <div class="cw-message-actions cw-message-actions-${s||"left"}">
      ${a&&h`
        <button
          class="cw-message-action-btn"
          onClick=${e}
          title="Edit message"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
          </svg>
        </button>
      `}
      <button
        class="cw-message-action-btn"
        onClick=${t}
        title="Retry from here"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 2v6h-6"></path>
          <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
          <path d="M3 22v-6h6"></path>
          <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
        </svg>
      </button>
    </div>
  `}function Yt({initialContent:e,onSave:t,onCancel:n}){let[s,a]=C(e),o=G(null);return W(()=>{o.current&&(o.current.focus(),o.current.setSelectionRange(s.length,s.length),o.current.style.height="auto",o.current.style.height=o.current.scrollHeight+"px")},[]),h`
    <div class="cw-inline-edit">
      <textarea
        ref=${o}
        class="cw-inline-edit-input"
        value=${s}
        onInput=${u=>{a(u.target.value),u.target.style.height="auto",u.target.style.height=u.target.scrollHeight+"px"}}
        onKeyDown=${u=>{u.key==="Enter"&&!u.shiftKey?(u.preventDefault(),s.trim()&&t(s.trim())):u.key==="Escape"&&n()}}
        rows="1"
      />
      <div class="cw-inline-edit-actions">
        <button
          class="cw-inline-edit-btn cw-inline-edit-cancel"
          onClick=${n}
          title="Cancel (Esc)"
        >Cancel</button>
        <button
          class="cw-inline-edit-btn cw-inline-edit-save"
          onClick=${()=>s.trim()&&t(s.trim())}
          disabled=${!s.trim()}
          title="Save & Resend (Enter)"
        >Save & Send</button>
      </div>
    </div>
  `}function kt({msg:e,debugMode:t,markdownParser:n,onEdit:s,onRetry:a,isLoading:o,messageIndex:l}){let[c,u]=C(!1),[i,d]=C(!1),[r,_]=C(!1),p=e.role==="user",k=e.role==="system",w=e.type==="tool_call",y=e.type==="tool_result",g=e.type==="error",$=e.type==="sub_agent_start",I=e.type==="sub_agent_end",N=e.type==="agent_context";if(k&&!t)return null;if($||I||N)return h`
      <div class="cw-agent-context ${$?"cw-agent-delegating":""} ${I?"cw-agent-returned":""}" style="position: relative;">
        <span class="cw-agent-context-icon">${$?"\u{1F517}":I?"\u2713":"\u{1F916}"}</span>
        <span class="cw-agent-context-text">${e.content}</span>
        ${e.metadata?.agentName&&h`
          <span class="cw-agent-context-name">${e.metadata.agentName}</span>
        `}
        ${t&&h`<${Oe} msg=${e} show=${i} onToggle=${()=>d(!i)} />`}
      </div>
    `;if(w||y){let S=e.metadata?.arguments||e.metadata?.result,E=v=>{if(typeof v=="string")try{return JSON.stringify(JSON.parse(v),null,2)}catch{return v}return JSON.stringify(v,null,2)};return h`
      <div class="cw-tool-message ${y?"cw-tool-result":"cw-tool-call"}" style="position: relative;">
        <span class="cw-tool-label" onClick=${()=>S&&u(!c)}>
          ${e.content}
          ${S&&h`<span class="cw-tool-expand">${c?"\u25BC":"\u25B6"}</span>`}
        </span>
        ${c&&S&&h`
          <pre class="cw-tool-details">${j(E(w?e.metadata.arguments:e.metadata.result))}</pre>
        `}
        ${t&&h`<${Oe} msg=${e} show=${i} onToggle=${()=>d(!i)} />`}
      </div>
    `}let J=["cw-message",p&&"cw-message-user",g&&"cw-message-error"].filter(Boolean).join(" "),z=`cw-message-row ${p?"cw-message-row-user":""}`,V=e.role==="assistant"?gt(e.content,n):j(e.content),K=e.files&&e.files.length>0,B=()=>K?h`
      <div class="cw-message-attachments">
        ${e.files.map(S=>S.type&&S.type.startsWith("image/")?h`
              <a class="cw-attachment-thumbnail" href=${S.url} target="_blank" title=${S.name}>
                <img src=${S.url} alt=${S.name} />
              </a>
            `:h`
            <a class="cw-attachment-file" href=${S.url} target="_blank" title=${S.name}>
              <span class="cw-attachment-icon">${ke(S.type)}</span>
              <span class="cw-attachment-info">
                <span class="cw-attachment-name">${S.name}</span>
                <span class="cw-attachment-size">${$e(S.size)}</span>
              </span>
            </a>
          `)}
      </div>
    `:null,q=S=>{_(!1),s&&s(l,S)},O=()=>{a&&a(l)};if(p&&r)return h`
      <div class=${z} style="position: relative;">
        ${B()}
        <${Yt}
          initialContent=${e.content}
          onSave=${q}
          onCancel=${()=>_(!1)}
        />
      </div>
    `;let f=p&&s&&a,T=e.role==="assistant"&&a&&!o;return h`
    <div class="${z} ${f||T?"cw-message-row-with-actions":""}">
      ${B()}
      ${f&&h`
        <div class="cw-user-actions-wrapper">
          <${$t}
            onEdit=${()=>_(!0)}
            onRetry=${O}
            isLoading=${o}
            position="left"
            showEdit=${!0}
          />
          <div class=${J} dangerouslySetInnerHTML=${{__html:V}} />
        </div>
      `}
      ${!f&&h`
        <div class=${J} dangerouslySetInnerHTML=${{__html:V}} />
      `}
      ${T&&h`
        <${$t}
          onRetry=${O}
          isLoading=${o}
          position="right"
          showEdit=${!1}
        />
      `}
      ${t&&h`<${Oe} msg=${e} show=${i} onToggle=${()=>d(!i)} />`}
    </div>
  `}function bt({messages:e,isLoading:t,hasMoreMessages:n,loadingMoreMessages:s,onLoadMore:a,onEditMessage:o,onRetryMessage:l,debugMode:c,markdownParser:u,emptyStateTitle:i,emptyStateMessage:d}){let r=G(null),_=G(!0),p=w=>{let y=w.target,g=y.scrollHeight-y.scrollTop-y.clientHeight<100;if(_.current=g,y.scrollTop<50&&n&&!s){let $=y.scrollHeight;a().then(()=>{let I=y.scrollHeight;y.scrollTop=I-$+y.scrollTop})}};W(()=>{let w=r.current;w&&_.current&&requestAnimationFrame(()=>{w.scrollTop=w.scrollHeight})},[e,t]),W(()=>{let w=r.current;w&&e.length<=2&&(_.current=!0,requestAnimationFrame(()=>{w.scrollTop=w.scrollHeight}))},[e.length]);let k=e.length===0;return h`
    <div class="cw-messages" ref=${r} onScroll=${p}>
      ${k&&h`
        <div class="cw-empty-state">
          <svg class="cw-empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <h3>${j(i)}</h3>
          <p>${j(d)}</p>
        </div>
      `}
      
      ${!k&&n&&h`
        <div class="cw-load-more" onClick=${a}>
          ${s?h`<span class="cw-spinner"></span><span>Loading...</span>`:h`<span>↑ Scroll up or click to load older messages</span>`}
        </div>
      `}
      
      ${e.map((w,y)=>h`
        <${kt}
          key=${w.id}
          msg=${w}
          messageIndex=${y}
          debugMode=${c}
          markdownParser=${u}
          onEdit=${o}
          onRetry=${l}
          isLoading=${t}
        />
      `)}
      
      ${t&&h`
        <div class="cw-message-row">
          <div class="cw-typing">
            <span class="cw-spinner"></span>
            <span>Thinking...</span>
          </div>
        </div>
      `}
    </div>
  `}var Ne=typeof window<"u"?window.SpeechRecognition||window.webkitSpeechRecognition:null;function Ct({onSend:e,onCancel:t,isLoading:n,placeholder:s,primaryColor:a,enableVoice:o=!0,enableFiles:l=!0}){let[c,u]=C(""),[i,d]=C([]),[r,_]=C(!1),[p,k]=C(!1),[w]=C(()=>!!Ne),y=G(null),g=G(null),$=G(null),I=G(!1);W(()=>{!n&&y.current&&y.current.focus()},[n]),W(()=>{y.current&&(y.current.style.height="auto",y.current.style.height=Math.min(y.current.scrollHeight,150)+"px")},[c]),W(()=>()=>{I.current=!1,$.current&&$.current.abort()},[]);let N=v=>{v.preventDefault(),(c.trim()||i.length>0)&&!n&&(e(c,i),u(""),d([]),y.current&&(y.current.style.height="auto"),g.current&&(g.current.value=""))},J=v=>{let D=Array.from(v.target.files||[]);D.length>0&&d(F=>[...F,...D])},z=v=>{d(D=>D.filter((F,m)=>m!==v))},V=v=>{v.preventDefault(),g.current&&!n&&g.current.click()},K=v=>{v.key==="Enter"&&!v.shiftKey&&(v.preventDefault(),N(v))},B=v=>{n&&t&&(v.preventDefault(),t())},q=()=>{if(!Ne||n)return;I.current=!0;let v=new Ne;v.continuous=!0,v.interimResults=!0,v.lang=navigator.language||"en-US";let D=c,F="";v.onstart=()=>{k(!0)},v.onresult=m=>{F="";for(let b=m.resultIndex;b<m.results.length;b++){let R=m.results[b][0].transcript;m.results[b].isFinal?D+=(D?" ":"")+R:F+=R}u(D+(F?" "+F:""))},v.onerror=m=>{if(m.error==="no-speech"||m.error==="aborted"){console.log("[ChatWidget] Speech recognition:",m.error,"- continuing...");return}console.warn("[ChatWidget] Speech recognition error:",m.error),I.current=!1,k(!1),u(D||c)},v.onend=()=>{if(I.current){console.log("[ChatWidget] Recognition paused, restarting...");try{v.start();return}catch(m){console.warn("[ChatWidget] Could not restart recognition:",m)}}k(!1),D&&u(D),$.current=null},$.current=v,v.start()},O=()=>{I.current=!1,$.current&&$.current.stop()},f=v=>{v.preventDefault(),p?O():q()},M=h`
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <rect x="2" y="2" width="10" height="10" rx="1" />
    </svg>
  `,T=h`
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" y1="19" x2="12" y2="23"></line>
      <line x1="8" y1="23" x2="16" y2="23"></line>
    </svg>
  `,x=h`
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
    </svg>
  `,S=o&&w,E=l;return h`
    <form class="cw-input-form" onSubmit=${N}>
      <input
        type="file"
        ref=${g}
        style="display: none"
        multiple
        onChange=${J}
      />
      ${i.length>0&&h`
        <div class="cw-file-chips">
          ${i.map((v,D)=>h`
            <div class="cw-file-chip" key=${D}>
              <span class="cw-file-chip-icon">${ke(v.type)}</span>
              <span class="cw-file-chip-name" title=${v.name}>${v.name.length>20?v.name.substring(0,17)+"...":v.name}</span>
              <span class="cw-file-chip-size">(${$e(v.size)})</span>
              <button
                type="button"
                class="cw-file-chip-remove"
                onClick=${()=>z(D)}
                title="Remove file"
              >×</button>
            </div>
          `)}
        </div>
      `}
      <textarea
        ref=${y}
        class="cw-input"
        placeholder=${j(s)}
        value=${c}
        onInput=${v=>u(v.target.value)}
        onKeyDown=${K}
        disabled=${n}
        rows="1"
      />
      ${E&&h`
        <button
          type="button"
          class="cw-attach-btn"
          onClick=${V}
          disabled=${n}
          title="Attach files"
        >
          ${x}
        </button>
      `}
      ${S&&h`
        <button
          type="button"
          class=${`cw-voice-btn ${p?"cw-voice-btn-recording":""}`}
          onClick=${f}
          disabled=${n}
          title=${p?"Stop recording":"Voice input"}
        >
          ${T}
        </button>
      `}
      <button
        type=${n?"button":"submit"}
        class=${`cw-send-btn ${n?"cw-send-btn-loading":""} ${n&&r?"cw-send-btn-stop":""}`}
        style=${{backgroundColor:n&&r?"#dc2626":a}}
        onClick=${B}
        onMouseEnter=${()=>_(!0)}
        onMouseLeave=${()=>_(!1)}
        title=${n?"Stop":"Send"}
      >
        ${n?r?M:h`<span class="cw-spinner"></span>`:"\u27A4"}
      </button>
    </form>
  `}function St({isOpen:e,conversations:t,conversationsLoading:n,currentConversationId:s,onClose:a,onNewConversation:o,onSwitchConversation:l}){return h`
    <div class="cw-sidebar ${e?"cw-sidebar-open":""}">
      <div class="cw-sidebar-header">
        <span>Conversations</span>
        <button class="cw-sidebar-close" onClick=${a}>✕</button>
      </div>
      
      <button class="cw-new-conversation" onClick=${o}>
        <span>+ New Conversation</span>
      </button>
      
      <div class="cw-conversation-list">
        ${n&&h`
          <div class="cw-sidebar-loading">
            <span class="cw-spinner"></span>
          </div>
        `}
        
        ${!n&&t.length===0&&h`
          <div class="cw-sidebar-empty">No conversations yet</div>
        `}
        
        ${t.map(c=>h`
          <div 
            key=${c.id}
            class="cw-conversation-item ${c.id===s?"cw-conversation-active":""}"
            onClick=${()=>l(c.id)}
          >
            <div class="cw-conversation-title">${j(c.title||"Untitled")}</div>
            <div class="cw-conversation-date">${mt(c.updatedAt||c.createdAt)}</div>
          </div>
        `)}
      </div>
    </div>
    
    <div 
      class="cw-sidebar-overlay ${e?"cw-sidebar-overlay-visible":""}" 
      onClick=${a}
    />
  `}function Tt({availableModels:e,selectedModel:t,onSelectModel:n,disabled:s}){let[a,o]=C(!1);if(!e||e.length===0)return null;let c=e.find(d=>d.id===t)?.name||"Select Model",u=()=>{s||o(!a)},i=d=>{n(d),o(!1)};return h`
    <div class="cw-model-selector">
      <button 
        class="cw-model-btn" 
        onClick=${u}
        disabled=${s}
        title="Select Model"
      >
        <span class="cw-model-icon">🤖</span>
        <span class="cw-model-name">${j(c)}</span>
        <span class="cw-model-chevron">${a?"\u25B2":"\u25BC"}</span>
      </button>
      
      ${a&&h`
        <div class="cw-model-dropdown">
          ${e.map(d=>h`
            <button 
              key=${d.id}
              class="cw-model-option ${d.id===t?"cw-model-option-selected":""}"
              onClick=${()=>i(d.id)}
            >
              <span class="cw-model-option-name">${j(d.name)}</span>
              <span class="cw-model-option-provider">${j(d.provider)}</span>
              ${d.description&&h`
                <span class="cw-model-option-desc">${j(d.description)}</span>
              `}
            </button>
          `)}
        </div>
      `}
    </div>
  `}var en={not_started:"\u25CB",in_progress:"\u25D0",complete:"\u25CF",cancelled:"\u2298"},tn={not_started:"Not Started",in_progress:"In Progress",complete:"Complete",cancelled:"Cancelled"};function nn({task:e,onUpdate:t,onRemove:n,depth:s=0}){let[a,o]=C(!1),[l,c]=C(e.name),u=A(()=>{let _={not_started:"in_progress",in_progress:"complete",complete:"not_started",cancelled:"not_started"};t(e.id,{state:_[e.state]||"not_started"})},[e,t]),i=A(()=>{l.trim()&&l!==e.name&&t(e.id,{name:l.trim()}),o(!1)},[e,l,t]),d=A(_=>{_.key==="Enter"&&i(),_.key==="Escape"&&(c(e.name),o(!1))},[i,e.name]),r=`cw-task-state-${e.state.replace("_","-")}`;return h`
    <div class="cw-task-item ${r}" style=${{paddingLeft:`${s*16+8}px`}}>
      <button 
        class="cw-task-state-btn" 
        onClick=${u}
        title=${tn[e.state]}
      >
        ${en[e.state]}
      </button>
      
      ${a?h`
        <input
          type="text"
          class="cw-task-edit-input"
          value=${l}
          onInput=${_=>c(_.target.value)}
          onBlur=${i}
          onKeyDown=${d}
          autoFocus
        />
      `:h`
        <span 
          class="cw-task-name" 
          onClick=${()=>o(!0)}
          title="Click to edit"
        >
          ${e.name}
        </span>
      `}
      
      <button 
        class="cw-task-remove-btn" 
        onClick=${()=>n(e.id)}
        title="Remove task"
      >
        ×
      </button>
    </div>
  `}function Mt({tasks:e,progress:t,isLoading:n,error:s,onUpdate:a,onRemove:o,onClear:l,onRefresh:c}){let u=A(r=>{let _=new Map,p=[];return r.forEach(k=>{_.set(k.id,{...k,children:[]})}),r.forEach(k=>{let w=_.get(k.id);k.parent_id&&_.has(k.parent_id)?_.get(k.parent_id).children.push(w):p.push(w)}),p},[]),i=A((r,_=0)=>h`
      <${nn}
        key=${r.id}
        task=${r}
        depth=${_}
        onUpdate=${a}
        onRemove=${o}
      />
      ${r.children?.map(p=>i(p,_+1))}
    `,[a,o]),d=u(e);return n&&e.length===0?h`<div class="cw-tasks-loading">Loading tasks...</div>`:h`
    <div class="cw-tasks-container">
      <div class="cw-tasks-header">
        <div class="cw-tasks-progress">
          <span class="cw-tasks-progress-text">
            ${t.completed}/${t.total} complete
          </span>
          <div class="cw-tasks-progress-bar">
            <div 
              class="cw-tasks-progress-fill" 
              style=${{width:`${t.percent_complete}%`}}
            />
          </div>
        </div>
        <div class="cw-tasks-actions">
          <button class="cw-tasks-action-btn" onClick=${c} title="Refresh">↻</button>
          ${e.length>0&&h`
            <button class="cw-tasks-action-btn" onClick=${l} title="Clear all">🗑</button>
          `}
        </div>
      </div>
      
      ${s&&h`<div class="cw-tasks-error">${s}</div>`}
      
      <div class="cw-tasks-list">
        ${d.length===0?h`
          <div class="cw-tasks-empty">
            <p>No tasks yet</p>
            <p class="cw-tasks-empty-hint">Tasks will appear here when the agent creates them</p>
          </div>
        `:d.map(r=>i(r))}
      </div>
    </div>
  `}function xt(e,t,n){let[s,a]=C([]),[o,l]=C(!1),[c,u]=C(null),[i,d]=C(()=>n?.get(e.conversationIdKey)||null),[r,_]=C(!1),[p,k]=C(!1),[w,y]=C(0),g=G(null),$=G(null);W(()=>{i&&n?.set(e.conversationIdKey,i)},[i,e.conversationIdKey,n]);let I=A(async(f,M,T)=>{g.current&&g.current.close();let x=e.apiPaths.runEvents.replace("{runId}",f),S=`${e.backendUrl}${x}`;M&&(S+=`?anonymous_token=${encodeURIComponent(M)}`);let E=new EventSource(S);g.current=E;let v="";E.addEventListener("assistant.message",F=>{try{let m=JSON.parse(F.data);e.onEvent&&e.onEvent("assistant.message",m.payload);let b=m.payload.content;b&&(v+=b,a(R=>{let X=R[R.length-1];return X?.role==="assistant"&&X.id.startsWith("assistant-stream-")?[...R.slice(0,-1),{...X,content:v}]:[...R,{id:"assistant-stream-"+Date.now(),role:"assistant",content:v,timestamp:new Date,type:"message"}]}))}catch(m){console.error("[ChatWidget] Parse error:",m)}}),E.addEventListener("tool.call",F=>{try{let m=JSON.parse(F.data);e.onEvent&&e.onEvent("tool.call",m.payload),a(b=>[...b,{id:"tool-call-"+Date.now(),role:"assistant",content:`\u{1F527} ${m.payload.name}`,timestamp:new Date,type:"tool_call",metadata:{toolName:m.payload.name,arguments:m.payload.arguments,toolCallId:m.payload.id}}])}catch(m){console.error("[ChatWidget] Parse error:",m)}}),E.addEventListener("tool.result",F=>{try{let m=JSON.parse(F.data);e.onEvent&&e.onEvent("tool.result",m.payload);let b=m.payload.result,R=b?.error;a(X=>[...X,{id:"tool-result-"+Date.now(),role:"system",content:R?`\u274C ${b.error}`:"\u2713 Done",timestamp:new Date,type:"tool_result",metadata:{toolName:m.payload.name,result:b,toolCallId:m.payload.tool_call_id}}])}catch(m){console.error("[ChatWidget] Parse error:",m)}}),E.addEventListener("custom",F=>{try{let m=JSON.parse(F.data);e.onEvent&&e.onEvent("custom",m.payload),m.payload?.type==="ui_control"&&e.onUIControl&&e.onUIControl(m.payload),m.payload?.type==="agent_context"&&a(b=>[...b,{id:"agent-context-"+Date.now(),role:"system",content:`\u{1F517} ${m.payload.agent_name||"Sub-agent"} is now handling this request`,timestamp:new Date,type:"agent_context",metadata:{agentKey:m.payload.agent_key,agentName:m.payload.agent_name,action:m.payload.action}}])}catch(m){console.error("[ChatWidget] Parse error:",m)}}),E.addEventListener("sub_agent.start",F=>{try{let m=JSON.parse(F.data);e.onEvent&&e.onEvent("sub_agent.start",m.payload),a(b=>[...b,{id:"sub-agent-start-"+Date.now(),role:"system",content:`\u{1F517} Delegating to ${m.payload.agent_name||m.payload.sub_agent_key||"sub-agent"}...`,timestamp:new Date,type:"sub_agent_start",metadata:{subAgentKey:m.payload.sub_agent_key,agentName:m.payload.agent_name,invocationMode:m.payload.invocation_mode}}])}catch(m){console.error("[ChatWidget] Parse error:",m)}}),E.addEventListener("sub_agent.end",F=>{try{let m=JSON.parse(F.data);e.onEvent&&e.onEvent("sub_agent.end",m.payload),a(b=>[...b,{id:"sub-agent-end-"+Date.now(),role:"system",content:`\u2713 ${m.payload.agent_name||"Sub-agent"} completed`,timestamp:new Date,type:"sub_agent_end",metadata:{subAgentKey:m.payload.sub_agent_key,agentName:m.payload.agent_name}}])}catch(m){console.error("[ChatWidget] Parse error:",m)}});let D=F=>{try{let m=JSON.parse(F.data);if(e.onEvent&&e.onEvent(m.type,m.payload),m.type==="run.failed"){let b=m.payload.error||"Agent run failed";u(b),a(R=>[...R,{id:"error-"+Date.now(),role:"system",content:`\u274C Error: ${b}`,timestamp:new Date,type:"error"}])}}catch(m){console.error("[ChatWidget] Parse error:",m)}l(!1),E.close(),g.current=null,v&&T&&T(v)};E.addEventListener("run.succeeded",D),E.addEventListener("run.failed",D),E.addEventListener("run.cancelled",D),E.addEventListener("run.timed_out",D),E.onerror=()=>{l(!1),E.close(),g.current=null}},[e]),N=A(async(f,M={},T={})=>{if(!f.trim()||o)return;let x=[],S={};typeof M=="function"?S={onAssistantMessage:M}:Array.isArray(M)?(x=M,S=T):S=M||{};let{model:E,onAssistantMessage:v,supersedeFromMessageIndex:D}=S;l(!0),u(null);let F={id:we(),role:"user",content:f.trim(),timestamp:new Date,type:"message",files:x.length>0?x.map(m=>({name:m.name,size:m.size,type:m.type})):void 0};a(m=>[...m,F]);try{let m=await t.getOrCreateSession(),b;if(x.length>0){let te=e.apiCaseStyle!=="camel",Ue=le=>te?He(le):le,Y=new FormData;Y.append(Ue("agentKey"),e.agentKey),i&&Y.append(Ue("conversationId"),i),Y.append("messages",JSON.stringify([{role:"user",content:f.trim()}])),Y.append("metadata",JSON.stringify(te?{...e.metadata,journey_type:e.defaultJourneyType}:{...e.metadata,journeyType:e.defaultJourneyType})),E&&Y.append("model",E),x.forEach(le=>{Y.append("files",le)}),b=t.getFetchOptions({method:"POST",body:Y},m)}else{let te=t.transformRequest({agentKey:e.agentKey,conversationId:i,messages:[{role:"user",content:f.trim()}],metadata:{...e.metadata,journeyType:e.defaultJourneyType},...E&&{model:E},...D!==void 0&&{supersedeFromMessageIndex:D}});b=t.getFetchOptions({method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(te)},m)}let R=await fetch(`${e.backendUrl}${e.apiPaths.runs}`,b);if(!R.ok){let te=await R.json().catch(()=>({}));throw new Error(te.error||`HTTP ${R.status}`)}let X=await R.json(),Z=t.transformResponse(X);$.current=Z.id,!i&&Z.conversationId&&d(Z.conversationId),await I(Z.id,m,v)}catch(m){u(m.message||"Failed to send message"),l(!1)}finally{$.current=null}},[e,t,i,o,I]),J=A(async()=>{let f=$.current;if(!(!f||!o))try{let M=e.apiPaths.cancelRun?e.apiPaths.cancelRun.replace("{runId}",f):`${e.apiPaths.runs}${f}/cancel/`;(await fetch(`${e.backendUrl}${M}`,t.getFetchOptions({method:"POST",headers:{"Content-Type":"application/json"}}))).ok&&(g.current&&(g.current.close(),g.current=null),l(!1),$.current=null,a(x=>[...x,{id:"cancelled-"+Date.now(),role:"system",content:"\u23F9 Run cancelled",timestamp:new Date,type:"cancelled"}]))}catch(M){console.error("[ChatWidget] Failed to cancel run:",M)}},[e,t,o]),z=A(()=>{a([]),d(null),u(null),_(!1),y(0),n?.set(e.conversationIdKey,null)},[e.conversationIdKey,n]),V=f=>{let M={id:we(),role:f.role,timestamp:f.timestamp?new Date(f.timestamp):new Date};if(f.role==="tool")return{...M,role:"system",content:"\u2713 Done",type:"tool_result",metadata:{result:f.content,toolCallId:f.toolCallId}};if(f.role==="assistant"&&f.toolCalls&&f.toolCalls.length>0)return f.toolCalls.map(x=>({id:we(),role:"assistant",content:`\u{1F527} ${x.function?.name||x.name||"tool"}`,timestamp:M.timestamp,type:"tool_call",metadata:{toolName:x.function?.name||x.name,arguments:x.function?.arguments||x.arguments,toolCallId:x.id}}));let T=typeof f.content=="string"?f.content:JSON.stringify(f.content);return f.role==="assistant"&&!T?.trim()?null:{...M,content:T,type:"message"}},K=A(async f=>{l(!0),a([]),d(f);try{let M=await t.getOrCreateSession(),x=`${e.backendUrl}${e.apiPaths.conversations}${f}/?limit=10&offset=0`,S=await fetch(x,t.getFetchOptions({method:"GET"},M));if(S.ok){let E=await S.json(),v=t.transformResponse(E);v.messages&&a(v.messages.flatMap(V).filter(Boolean)),_(v.hasMore||!1),y(v.messages?.length||0)}else S.status===404&&(d(null),n?.set(e.conversationIdKey,null))}catch(M){console.error("[ChatWidget] Failed to load conversation:",M)}finally{l(!1)}},[e,t,n]),B=A(async()=>{if(!(!i||p||!r)){k(!0);try{let f=await t.getOrCreateSession(),T=`${e.backendUrl}${e.apiPaths.conversations}${i}/?limit=10&offset=${w}`,x=await fetch(T,t.getFetchOptions({method:"GET"},f));if(x.ok){let S=await x.json(),E=t.transformResponse(S);if(E.messages?.length>0){let v=E.messages.flatMap(V).filter(Boolean);a(D=>[...v,...D]),y(D=>D+E.messages.length),_(E.hasMore||!1)}else _(!1)}}catch(f){console.error("[ChatWidget] Failed to load more messages:",f)}finally{k(!1)}}},[e,t,i,w,p,r]),q=A(async(f,M,T={})=>{if(o)return;let x=s[f];if(!x||x.role!=="user")return;let S=s.slice(0,f);a(S),await N(M,{...T,supersedeFromMessageIndex:f})},[s,o,N]),O=A(async(f,M={})=>{if(o)return;let T=s[f];if(!T)return;let x=f,S=T;if(T.role==="assistant"){for(let v=f-1;v>=0;v--)if(s[v].role==="user"){x=v,S=s[v];break}if(S.role!=="user")return}else if(T.role!=="user")return;let E=s.slice(0,x);a(E),await N(S.content,{...M,supersedeFromMessageIndex:x})},[s,o,N]);return W(()=>()=>{g.current&&g.current.close()},[]),{messages:s,isLoading:o,error:c,conversationId:i,hasMoreMessages:r,loadingMoreMessages:p,sendMessage:N,cancelRun:J,clearMessages:z,loadConversation:K,loadMoreMessages:B,setConversationId:d,editMessage:q,retryMessage:O}}function Et(e,t,n){let[s,a]=C([]),[o,l]=C(null),[c,u]=C(null),[i,d]=C(!1);W(()=>{(async()=>{if(e.showModelSelector){d(!0);try{let k=await fetch(`${e.backendUrl}${e.apiPaths.models}`,t.getFetchOptions({method:"GET"}));if(k.ok){let w=await k.json(),y=w.models||[];a(y),u(w.default);let g=n?.get(e.modelKey);g&&y.some($=>$.id===g)?l(g):l(w.default)}}catch(k){console.warn("[ChatWidget] Failed to load models:",k)}finally{d(!1)}}})()},[e.backendUrl,e.apiPaths.models,e.showModelSelector,e.modelKey,t,n]);let r=A(p=>{l(p),n?.set(e.modelKey,p)},[e.modelKey,n]),_=A(()=>s.find(p=>p.id===o)||null,[s,o]);return{availableModels:s,selectedModel:o,defaultModel:c,isLoading:i,selectModel:r,getSelectedModelInfo:_}}function It(e,t){let[n,s]=C(null),[a,o]=C(!1),[l,c]=C(null),u=e.apiPaths?.tasks||"/api/agent/tasks/",i=A(async()=>{o(!0),c(null);try{let w=`${e.backendUrl}${u}`,y=await fetch(w,t.getFetchOptions({method:"GET"}));if(y.ok){let g=await y.json();s(g)}else{let g=await y.json().catch(()=>({}));c(g.error||"Failed to load tasks")}}catch(w){console.error("[useTasks] Failed to load task list:",w),c("Failed to load tasks")}finally{o(!1)}},[e.backendUrl,u,t]),d=A(async w=>{if(!n)return null;try{let y=`${e.backendUrl}${u}${n.id}/add_task/`,g=await fetch(y,t.getFetchOptions({method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(w)}));if(g.ok){let $=await g.json();return await i(),$}else{let $=await g.json().catch(()=>({}));return c($.error||"Failed to add task"),null}}catch(y){return console.error("[useTasks] Failed to add task:",y),c("Failed to add task"),null}},[e.backendUrl,u,n,t,i]),r=A(async(w,y)=>{if(!n)return null;try{let g=`${e.backendUrl}${u}${n.id}/update_task/${w}/`,$=await fetch(g,t.getFetchOptions({method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(y)}));if($.ok){let I=await $.json();return await i(),I}else{let I=await $.json().catch(()=>({}));return c(I.error||"Failed to update task"),null}}catch(g){return console.error("[useTasks] Failed to update task:",g),c("Failed to update task"),null}},[e.backendUrl,u,n,t,i]),_=A(async w=>{if(!n)return!1;try{let y=`${e.backendUrl}${u}${n.id}/remove_task/${w}/`,g=await fetch(y,t.getFetchOptions({method:"DELETE"}));if(g.ok)return await i(),!0;{let $=await g.json().catch(()=>({}));return c($.error||"Failed to remove task"),!1}}catch(y){return console.error("[useTasks] Failed to remove task:",y),c("Failed to remove task"),!1}},[e.backendUrl,u,n,t,i]),p=A(async()=>{if(!n)return!1;try{let w=`${e.backendUrl}${u}${n.id}/clear/`,y=await fetch(w,t.getFetchOptions({method:"POST"}));if(y.ok)return await i(),!0;{let g=await y.json().catch(()=>({}));return c(g.error||"Failed to clear tasks"),!1}}catch(w){return console.error("[useTasks] Failed to clear tasks:",w),c("Failed to clear tasks"),!1}},[e.backendUrl,u,n,t,i]),k=A(()=>c(null),[]);return{taskList:n,tasks:n?.tasks||[],progress:n?.progress||{total:0,completed:0,percent_complete:0},isLoading:a,error:l,loadTaskList:i,addTask:d,updateTask:r,removeTask:_,clearTasks:p,clearError:k}}function At(e,t,n){let s=i=>!i||typeof i!="object"||e.apiCaseStyle==="camel"?i:ve(i),a=i=>!i||typeof i!="object"||e.apiCaseStyle==="snake"?i:ye(i),o=()=>e.authStrategy?e.authStrategy:e.authToken?"token":e.apiPaths.anonymousSession||e.anonymousSessionEndpoint?"anonymous":"none",l=(i=null)=>{let d=o(),r={},_=i||e.authToken||t().authToken;if(d==="token"&&_){let p=e.authHeader||"Authorization",k=e.authTokenPrefix!==void 0?e.authTokenPrefix:"Token";r[p]=k?`${k} ${_}`:_}else if(d==="jwt"&&_){let p=e.authHeader||"Authorization",k=e.authTokenPrefix!==void 0?e.authTokenPrefix:"Bearer";r[p]=k?`${k} ${_}`:_}else if(d==="anonymous"&&_){let p=e.authHeader||e.anonymousTokenHeader||"X-Anonymous-Token";r[p]=_}if(d==="session"){let p=vt(e.csrfCookieName);p&&(r["X-CSRFToken"]=p)}return r};return{getAuthStrategy:o,getAuthHeaders:l,getFetchOptions:(i={},d=null)=>{let r=o(),_={...i};return _.headers={..._.headers,...l(d)},r==="session"&&(_.credentials="include"),_},getOrCreateSession:async()=>{let i=o(),d=t();if(i!=="anonymous")return e.authToken||d.authToken;if(d.authToken)return d.authToken;let r=e.anonymousTokenKey||e.sessionTokenKey,_=d.storage?.get(r);if(_)return n(p=>({...p,authToken:_})),_;try{let p=e.anonymousSessionEndpoint||e.apiPaths.anonymousSession,k=await fetch(`${e.backendUrl}${p}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(k.ok){let w=await k.json();return n(y=>({...y,authToken:w.token})),d.storage?.set(r,w.token),w.token}}catch(p){console.warn("[ChatWidget] Failed to create session:",p)}return null},transformRequest:s,transformResponse:a}}function Dt({config:e,onStateChange:t,markdownParser:n,apiRef:s}){let[a,o]=C(e.embedded||e.forceOpen===!0),[l,c]=C(!1),[u,i]=C(!1),[d,r]=C(!1),[_,p]=C([]),[k,w]=C("chat"),[y,g]=C(!1),[$,I]=C(e.enableTTS),[N,J]=C(!1),[z,V]=C(null);W(()=>{e.forceOpen!==void 0&&o(e.forceOpen)},[e.forceOpen]);let K=ie(()=>yt(e.containerId),[e.containerId]),[B,q]=C(e.authToken||null),O=ie(()=>At(e,()=>({authToken:B,storage:K}),X=>{let Z=X({authToken:B,storage:K});Z.authToken!==B&&q(Z.authToken)}),[e,B,K]),f=xt(e,O,K),M=Et(e,O,K),T=It(e,O);W(()=>{for(let b=f.messages.length-1;b>=0;b--){let R=f.messages[b];if(R.type==="sub_agent_start"){V({key:R.metadata?.subAgentKey,name:R.metadata?.agentName});return}if(R.type==="sub_agent_end"){V(null);return}}},[f.messages]),W(()=>{let b=K.get(e.conversationIdKey);b&&f.loadConversation(b)},[]),W(()=>{t&&t({isOpen:a,isExpanded:l,debugMode:u,messages:f.messages,conversationId:f.conversationId,isLoading:f.isLoading,error:f.error})},[a,l,u,f.messages,f.conversationId,f.isLoading,f.error]);let x=A(async()=>{if(e.showConversationSidebar){g(!0);try{let b=`${e.backendUrl}${e.apiPaths.conversations}?agent_key=${encodeURIComponent(e.agentKey)}`,R=await fetch(b,O.getFetchOptions({method:"GET"}));if(R.ok){let X=await R.json();p(X.results||X)}}catch(b){console.error("[ChatWidget] Failed to load conversations:",b),p([])}finally{g(!1)}}},[e,O]),S=A(()=>{let b=!d;r(b),b&&x()},[d,x]),E=A(b=>{b!==f.conversationId&&f.loadConversation(b),r(!1)},[f]),v=A(()=>{f.clearMessages(),r(!1)},[f]),D=A(b=>{f.sendMessage(b,{model:M.selectedModel,onAssistantMessage:R=>{}})},[f,$,M.selectedModel]),F=A(b=>{w(b),b==="tasks"&&T.loadTaskList()},[T]);if(W(()=>{s&&(s.current={open:()=>o(!0),close:()=>o(!1),send:b=>D(b),clearMessages:()=>f.clearMessages(),toggleTTS:()=>I(b=>!b),stopSpeech:()=>J(!1),setAuth:b=>{b.token!==void 0&&q(b.token)},clearAuth:()=>q(null)})},[f,s,D]),!e.embedded&&!a)return h`
      <button 
        class="cw-fab" 
        style=${{backgroundColor:e.primaryColor}}
        onClick=${()=>o(!0)}
      >
        <svg class="cw-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
    `;let m=["cw-widget",l&&"cw-widget-expanded",e.embedded&&"cw-widget-embedded"].filter(Boolean).join(" ");return h`
    <div class=${m} style=${{"--cw-primary":e.primaryColor}}>
      ${e.showConversationSidebar&&h`
        <${St}
          isOpen=${d}
          conversations=${_}
          conversationsLoading=${y}
          currentConversationId=${f.conversationId}
          onClose=${()=>r(!1)}
          onNewConversation=${v}
          onSwitchConversation=${E}
        />
      `}
      
      <${wt}
        config=${e}
        debugMode=${u}
        isExpanded=${l}
        isSpeaking=${N}
        messagesCount=${f.messages.length}
        isLoading=${f.isLoading}
        currentAgent=${z}
        onClose=${()=>o(!1)}
        onToggleExpand=${()=>c(!l)}
        onToggleDebug=${()=>i(!u)}
        onToggleTTS=${()=>I(!$)}
        onClear=${f.clearMessages}
        onToggleSidebar=${S}
      />

      ${e.showTasksTab!==!1&&h`
        <div class="cw-tabs">
          <button
            class=${`cw-tab ${k==="chat"?"cw-tab-active":""}`}
            onClick=${()=>F("chat")}
          >
            Chat
          </button>
          <button
            class=${`cw-tab ${k==="tasks"?"cw-tab-active":""}`}
            onClick=${()=>F("tasks")}
          >
            Tasks ${T.progress.total>0?h`<span class="cw-tab-badge">${T.progress.completed}/${T.progress.total}</span>`:""}
          </button>
        </div>
      `}

      ${u&&h`<div class="cw-status-bar"><span>🐛 Debug</span></div>`}

      ${k==="chat"?h`
        <${bt}
          messages=${f.messages}
          isLoading=${f.isLoading}
          hasMoreMessages=${f.hasMoreMessages}
          loadingMoreMessages=${f.loadingMoreMessages}
          onLoadMore=${f.loadMoreMessages}
          onEditMessage=${f.editMessage}
          onRetryMessage=${f.retryMessage}
          debugMode=${u}
          markdownParser=${n}
          emptyStateTitle=${e.emptyStateTitle}
          emptyStateMessage=${e.emptyStateMessage}
        />

        ${f.error&&h`<div class="cw-error-bar">${f.error}</div>`}

        ${e.showModelSelector&&M.availableModels.length>0&&h`
          <${Tt}
            availableModels=${M.availableModels}
            selectedModel=${M.selectedModel}
            onSelectModel=${M.selectModel}
            disabled=${f.isLoading}
          />
        `}

        <${Ct}
          onSend=${D}
          onCancel=${f.cancelRun}
          isLoading=${f.isLoading}
          placeholder=${e.placeholder}
          primaryColor=${e.primaryColor}
          enableVoice=${e.enableVoice}
        />
      `:h`
        <${Mt}
          tasks=${T.tasks}
          progress=${T.progress}
          isLoading=${T.isLoading}
          error=${T.error}
          onUpdate=${T.updateTask}
          onRemove=${T.removeTask}
          onClear=${T.clearTasks}
          onRefresh=${T.loadTaskList}
        />
      `}
    </div>
  `}var Rt={backendUrl:"http://localhost:8000",agentKey:"default-agent",title:"Chat Assistant",subtitle:"How can we help you today?",primaryColor:"#0066cc",position:"bottom-right",defaultJourneyType:"general",enableDebugMode:!0,enableAutoRun:!0,journeyTypes:{},customerPrompts:{},placeholder:"Type your message...",emptyStateTitle:"Start a Conversation",emptyStateMessage:"Send a message to get started.",authStrategy:null,authToken:null,authHeader:null,authTokenPrefix:null,anonymousSessionEndpoint:null,anonymousTokenKey:"chat_widget_anonymous_token",onAuthError:null,anonymousTokenHeader:"X-Anonymous-Token",conversationIdKey:"chat_widget_conversation_id",sessionTokenKey:"chat_widget_session_token",apiPaths:{anonymousSession:"/api/accounts/anonymous-session/",conversations:"/api/agent-runtime/conversations/",runs:"/api/agent-runtime/runs/",runEvents:"/api/agent-runtime/runs/{runId}/events/",simulateCustomer:"/api/agent-runtime/simulate-customer/",ttsVoices:"/api/tts/voices/",ttsSetVoice:"/api/tts/set-voice/",models:"/api/agent-runtime/models/"},apiCaseStyle:"auto",showConversationSidebar:!0,showClearButton:!0,showDebugButton:!0,showTTSButton:!0,showVoiceSettings:!0,showExpandButton:!0,showModelSelector:!1,enableVoice:!0,modelKey:"chat_widget_selected_model",autoRunDelay:1e3,autoRunMode:"automatic",enableTTS:!1,ttsProxyUrl:null,elevenLabsApiKey:null,ttsVoices:{assistant:null,user:null},ttsModel:"eleven_turbo_v2_5",ttsSettings:{stability:.5,similarity_boost:.75,style:0,use_speaker_boost:!0},availableVoices:[],onEvent:null,containerId:null,embedded:!1,metadata:{}};function Pt(e){let t={...Rt.apiPaths,...e.apiPaths||{}};return{...Rt,...e,apiPaths:t}}var be=new Map,sn=0,P=null,Le=class{constructor(t={}){this.instanceId=`cw-${++sn}`,this.config=Pt(t),this.container=null,this._state={},this._apiRef={current:null},be.set(this.instanceId,this)}_handleStateChange=t=>{this._state=t};init(){if(this.config.containerId){if(this.container=document.getElementById(this.config.containerId),!this.container)return console.error(`[ChatWidget] Container not found: ${this.config.containerId}`),this;this.container.classList.add("cw-container-embedded")}else this.container=document.createElement("div"),this.container.id=this.instanceId,this.container.className=`cw-container cw-position-${this.config.position}`,document.body.appendChild(this.container);return this._render(),console.log(`[ChatWidget] Instance ${this.instanceId} initialized`),this}_render(t={}){this.container&&me(h`<${Dt}
        config=${{...this.config,...t}}
        onStateChange=${this._handleStateChange}
        markdownParser=${Ce._enhancedMarkdownParser}
        apiRef=${this._apiRef}
      />`,this.container)}destroy(){this.container&&(me(null,this.container),this.config.containerId?this.container.classList.remove("cw-container-embedded"):this.container.remove(),this.container=null),be.delete(this.instanceId),console.log(`[ChatWidget] Instance ${this.instanceId} destroyed`)}open(){this._apiRef.current?this._apiRef.current.open():this._render({forceOpen:!0})}close(){this._apiRef.current?this._apiRef.current.close():this._render({forceOpen:!1})}send(t){this._apiRef.current&&this._apiRef.current.send(t)}clearMessages(){this._apiRef.current&&this._apiRef.current.clearMessages()}toggleTTS(){this._apiRef.current&&this._apiRef.current.toggleTTS()}stopSpeech(){this._apiRef.current&&this._apiRef.current.stopSpeech()}setAuth(t){this._apiRef.current&&this._apiRef.current.setAuth(t)}clearAuth(){this._apiRef.current&&this._apiRef.current.clearAuth()}getState(){return{...this._state}}getConfig(){return{...this.config}}updateMetadata(t){this.config.metadata={...this.config.metadata,...t},this._render(),console.log(`[ChatWidget] Instance ${this.instanceId} metadata updated:`,t)}updateConfig(t){this.config={...this.config,...t},this._render(),console.log(`[ChatWidget] Instance ${this.instanceId} config updated`)}};function Ft(e={}){return new Le(e).init()}function on(e={}){return P&&P.destroy(),P=Ft(e),P}function an(){P&&(P.destroy(),P=null)}function rn(){P&&P.open()}function ln(){P&&P.close()}function cn(e){P&&P.send(e)}function un(){P&&P.clearMessages()}function dn(){P&&P.toggleTTS()}function _n(){P&&P.stopSpeech()}function pn(e){P&&P.setAuth(e)}function fn(){P&&P.clearAuth()}function hn(){return P?P.getState():null}function mn(){return P?P.getConfig():null}var Ce={createInstance:Ft,getInstance:e=>be.get(e),getAllInstances:()=>Array.from(be.values()),init:on,destroy:an,open:rn,close:ln,send:cn,clearMessages:un,toggleTTS:dn,stopSpeech:_n,setAuth:pn,clearAuth:fn,getState:hn,getConfig:mn,_enhancedMarkdownParser:null};var gn=Ce;typeof window<"u"&&(window.ChatWidget=Ce);return Wt(yn);})();
