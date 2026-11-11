const fs=require('fs'),vm=require('vm'),assert=require('assert');
const mode=process.argv[2]||'ai';
global.window=global; global.location={hash:process.argv[3]||''};global.history={replaceState(){}};
const elements={};let shown,hit=-1,requests=0;
global.document={getElementById(id){return elements[id]??={value:mode,classList:{add(){},remove(){}},listeners:{},addEventListener(k,f){this.listeners[k]=f;}};}};
global.BoardView=class{setState(s){shown=s;}hitTest(){return hit;}pulseAt(){}};
const nativeFetch=fetch;
global.fetch=(path,opts)=>{requests++;return nativeFetch((process.env.TEST_BASE_URL||'http://127.0.0.1:5000')+path,opts)};
const root=process.env.FRONTEND_ROOT||require('path').join(__dirname,'../static/js');
for(const name of ['board_data.js','rules_stub.js','api.js','game.js'])vm.runInThisContext(fs.readFileSync(root+'/'+name,'utf8'),{filename:name});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function until(p){for(let i=0;i<150;i++){if(p())return;await wait(40)}throw Error('timeout '+elements.hint.textContent)}
function clickMove(){const moves=RULES.legalMoves(shown),m=moves.find(m=>m.kind==='eat')||moves[0];if(m.from>=0){hit=m.from;elements.board.listeners.click({});}hit=m.to;elements.board.listeners.click({});}
(async()=>{
 if(location.hash){await wait(650);assert.equal(requests,0);console.log('PASS demo '+location.hash);return;}
 if(mode==='ai-king'){
   await until(()=>shown.ply===1);assert.equal(shown.turn,2);assert.equal(elements['btn-undo'].disabled,true);
   elements['btn-undo'].listeners.click();assert.equal(shown.ply,1);
   clickMove();await until(()=>shown.ply===3);elements['btn-undo'].listeners.click();assert.equal(shown.ply,1);assert.equal(shown.turn,2);
 }else{
   clickMove();await until(()=>shown.ply===(mode==='human'?1:2));elements['btn-undo'].listeners.click();assert.equal(shown.ply,0);
 }
 console.log('PASS moves+undo '+mode);
 // Discard an in-flight move after restarting; also switch mode to prevent opening AI.
 clickMove();elements['mode-select'].value='human';elements['mode-select'].listeners.change();await wait(650);assert.equal(shown.ply,0);
 console.log('PASS stale response discarded '+mode);
})().catch(e=>{console.error(e);process.exitCode=1});
