/* 与 Flask 同源运行；不使用阻塞式 XMLHttpRequest。 */
window.API = {
  async request(path, data) {
    const response = await fetch(path, {
      method: data === undefined ? 'GET' : 'POST',
      headers: {'Content-Type': 'application/json'},
      body: data === undefined ? undefined : JSON.stringify(data),
      signal: AbortSignal.timeout(15000)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '请求失败');
    return result;
  },
  async ai(state) {
    const job = await this.request('/api/ai', {state});
    const start = Date.now();
    while (Date.now() - start < 60000) {
      const result = await this.request('/api/tasks/' + job.taskId);
      if (result.status === 'done') return result.move;
      await new Promise(resolve => setTimeout(resolve, 150));
    }
    throw new Error('AI 等待超时，请重新开始；后台线程可能仍在计算');
  }
};
window.AI = {chooseMove: state => window.API.ai(state)};
