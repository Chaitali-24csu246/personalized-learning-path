export function usernameEmail(username,domain){const name=username.trim().toLowerCase();if(!/^[a-z][a-z0-9_-]{2,39}$/.test(name))throw Error('Use a username of 3–40 letters, numbers, underscores or hyphens.');return `${name}@${domain}`;}
export class CloudStore{
 constructor(client){this.client=client;this.user=null;this.account=null;this.version=0;}
 async signIn(username,password,domain){const {error}=await this.client.auth.signInWithPassword({email:usernameEmail(username,domain),password});if(error)throw Error('Sign-in failed. Check your username and password.');return this.loadAccount();}
 async loadAccount(){const {data,error}=await this.client.auth.getUser();if(error||!data.user)throw Error('Please sign in again.');this.user=data.user;const result=await this.client.from('profiles').select('id,username,display_name,role').eq('id',this.user.id).single();if(result.error)throw Error('Account setup is incomplete. Contact the administrator.');this.account=result.data;return this.account;}
 async loadProgress(){const {data,error}=await this.client.from('student_progress').select('payload,version').eq('user_id',this.user.id).maybeSingle();if(error)throw error;this.version=data?.version||0;return data?.payload||null;}
 async saveProgress(payload){const {data,error}=await this.client.rpc('save_my_progress',{expected_version:this.version,new_payload:payload});if(error)throw Error(error.message.includes('progress_conflict')?'Progress changed in another tab/device. Export a backup, then reload before continuing.':error.message);this.version=data;}
 async requestTopic(subject,topic,details){const {error}=await this.client.from('topic_requests').insert({user_id:this.user.id,subject,topic,details});if(error)throw error;}
 async requests(){let q=this.client.from('topic_requests').select('*').order('created_at',{ascending:false});if(this.account.role!=='admin')q=q.eq('user_id',this.user.id);const {data,error}=await q;if(error)throw error;return data;}
 async catalog(){const {data,error}=await this.client.from('course_catalog').select('*').eq('id',1).maybeSingle();if(error)throw error;return data||{revision:0,payload:{courses:[],topicOverrides:[],activities:[],removedTopics:[]}};}
 async saveCatalog(revision,payload){const {data,error}=await this.client.rpc('save_catalog',{expected_revision:revision,new_payload:payload});if(error)throw error;return data;}
 async password(password){if(password.length<12)throw Error('Use at least 12 characters.');const {error}=await this.client.auth.updateUser({password});if(error)throw error;}
 async signOut(){const {error}=await this.client.auth.signOut();if(error)throw error;this.user=null;this.account=null;}
}
// Serialises saves, coalesces edits, and retains the newest snapshot on failure.
export class SaveQueue{
 constructor(write,onStatus=()=>{}){this.write=write;this.onStatus=onStatus;this.pending=null;this.running=null;this.failure=null;}
 enqueue(value){this.pending=JSON.parse(JSON.stringify(value));this.onStatus('Unsaved changes');}
 async flush(){if(this.running){await this.running;return this.pending?this.flush():undefined;}if(!this.pending)return;if(this.failure)throw this.failure;
 this.running=(async()=>{while(this.pending){const item=this.pending;this.pending=null;this.onStatus('Saving…');try{await this.write(item);this.onStatus('Saved to your account');}catch(e){if(!this.pending)this.pending=item;this.failure=e;this.onStatus('Not saved — export backup');throw e;}}})();try{await this.running;}finally{this.running=null;}}
 retry(){this.failure=null;return this.flush();}
}
