import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { interval } from 'rxjs';

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  api = 'http://127.0.0.1:8000'; schedule: any = { equipment: [], operations: [], violations: [] }; state: any = { readings: [], predictions: [], commands: [] };
  start = '2026-10-01'; end = '2026-10-20'; selected: any; error = ''; feedValue = 8;
  constructor(private http: HttpClient) {}
  ngOnInit() { this.load(); interval(3000).subscribe(() => this.loadState()); }
  load() { this.http.get<any>(`${this.api}/api/schedule?start_date=${this.start}&end_date=${this.end}`).subscribe({next: x => this.schedule=x, error: e => this.error=e.message}); this.loadState(); }
  loadState() { this.http.get<any>(`${this.api}/api/control/state`).subscribe({next: x => this.state=x, error: e => this.error=e.message}); }
  violations(op: any) { return this.schedule.violations.filter((v:any) => v.operation_ids.includes(op.id)); }
  select(op:any) { this.selected = {...op}; }
  save() { this.http.put(`${this.api}/api/unit_operations/${this.selected.id}`, this.selected).subscribe({next: () => { this.selected=null; this.load(); }, error: e => this.error=JSON.stringify(e.error.detail)}); }
  command() { const now=this.state.current_process_time_h || 0; this.http.post(`${this.api}/command`, {setpoint_name:'feed_rate', value:this.feedValue, unit:'mL/h', apply_at_time_h:now + 5/60, source:'manual'}).subscribe({next:()=>this.loadState(), error:e=>{this.error=JSON.stringify(e.error.detail);this.loadState();}}); }
  left(op:any) { const days=(new Date(op.start_date).getTime()-new Date(this.start).getTime())/86400000; return Math.max(0, days*42); }
  width(op:any) { return Math.max(32, (new Date(op.end_date).getTime()-new Date(op.start_date).getTime())/86400000*42); }
  series(name:string) { return this.state.readings.filter((r:any) => r.signal_name === name); }
  activePredictions() { const now=this.state.current_process_time_h || 0; return this.state.predictions.filter((p:any) => p.made_at_process_time_h >= now - 0.12); }
  range() { const times=[...this.series('DO'),...this.activePredictions()].map((x:any)=>x.process_time_h ?? x.target_process_time_h); return times.length ? [Math.min(...times),Math.max(...times)] : [0,1]; }
  points(name:string, max:number) { const [a,b]=this.range(); return this.series(name).map((r:any)=>`${90+(r.process_time_h-a)/(b-a)*740},${180-r.value/max*140}`).join(' '); }
  forecastPoints() { const [a,b]=this.range(); return this.activePredictions().map((p:any)=>`${90+(p.target_process_time_h-a)/(b-a)*740},${180-p.value/100*140}`).join(' '); }
  commandX(c:any) { const [a,b]=this.range(); return 90+(c.apply_at_time_h-a)/(b-a)*740; }
  visibleCommands() { const [a,b]=this.range(); return this.state.commands.filter((c:any) => c.apply_at_time_h >= a && c.apply_at_time_h <= b); }
  forecast() { this.http.post(`${this.api}/api/forecast`, {}).subscribe({next:()=>this.loadState(), error:e=>this.error=JSON.stringify(e.error.detail)}); }
}
