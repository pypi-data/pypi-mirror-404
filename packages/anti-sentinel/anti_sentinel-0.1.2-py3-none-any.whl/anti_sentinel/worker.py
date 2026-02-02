import asyncio
import json
from anti_sentinel.services.queue import QueueService
from anti_sentinel.container import ServiceContainer

# We need a way to map job types to Agent classes dynamically.
# For V1, we will hardcode a "Generic Agent Runner".

async def start_worker():
    queue = QueueService.get_instance()
    container = ServiceContainer.get_instance()
    
    print("👷 Background Worker Started. Waiting for jobs...")
    
    while True:
        try:
            # 1. Check for work
            job = await queue.fetch_pending()
            
            if job:
                print(f"👷 Picking up Job: {job['job_id']}")
                data = json.loads(job['input_data'])
                
                # 2. Instantiate the Agent dynamically
                # (In a real app, 'agent_class' would be passed in the job data)
                # For now, we assume we are running the 'ContentWriterAgent' 
                # We import it here to avoid circular imports during startup
                
                # TODO: In V2, use a "Job Registry" to find the right class
                from app.agents.writer import ContentWriterAgent 
                
                agent = ContentWriterAgent(name="BackgroundBot", user_id="worker_1")
                
                # 3. Run the Agent
                result = await agent.think(data['topic'])
                
                # 4. Save Result
                await queue.complete(job['job_id'], result)
                print(f"✅ Job {job['job_id']} Completed.")
            
            else:
                # No work? Sleep for 2 seconds to save CPU
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Worker Error: {e}")
            await asyncio.sleep(5)