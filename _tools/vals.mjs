import { readFileSync } from 'node:fs';
const src = readFileSync(process.argv[2], 'utf8');
const extra = JSON.parse(process.argv[3] || '{}');
const js = src.split('data-dc-script')[1].split('>').slice(1).join('>').split('</script>')[0];
class DCLogic { constructor(p){ this.props = p || {}; this.state = {}; } setState(){} }
const C = new Function('DCLogic', js + '\nreturn Component;')(DCLogic);
const c = new C({}); Object.assign(c.state, extra);
console.log(JSON.stringify(c.renderVals()));
