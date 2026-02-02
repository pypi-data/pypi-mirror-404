import{g}from"./ajv-Cpj98o6Y.js";var C={exports:{}},h;function v(){if(h)return C.exports;h=1;/*
 * @version    1.4.0
 * @date       2015-10-26
 * @stability  3 - Stable
 * @author     Lauri Rooden (https://github.com/litejs/natural-compare-lite)
 * @license    MIT License
 */var x=function(u,l){var a,n,t=1,p=0,m=0,s=String.alphabet;function i(e,f,r){if(r){for(a=f;r=i(e,a),r<76&&r>65;)++a;return+e.slice(f-1,a)}return r=s&&s.indexOf(e.charAt(f)),r>-1?r+76:(r=e.charCodeAt(f)||0,r<45||r>127?r:r<46?65:r<48?r-1:r<58?r+18:r<65?r-11:r<91?r+11:r<97?r-37:r<123?r+5:r-63)}if((u+="")!=(l+="")){for(;t;)if(n=i(u,p++),t=i(l,m++),n<76&&t<76&&n>66&&t>66&&(n=i(u,p,p),t=i(l,m,p=a),m=a),n!=t)return n<t?-1:1}return 0};try{C.exports=x}catch{String.naturalCompare=x}return C.exports}var A=v();const o=g(A);export{o as n};
