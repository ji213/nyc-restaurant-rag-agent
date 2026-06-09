import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# A print lock ensures console lines from different threads don't jumble together
### When multiple background threads execute simultaneously, they all share access to the same system standard output (your console terminal). 
### If Thread A and Thread B print at the exact same millisecond, their text outputs wrap over each other, resulting in corrupted console logs.
print_lock = threading.Lock()

def mock_api_worker(batch_id, semaphore):
    """
    This represents our worker thread performing the OpenAI embedding 
    and Pinecone upload steps.
    """

    #unique system thread ID
    thread_id = threading.get_ident()
    
    # wait for print lock to free up to print to console
    with print_lock:
        print(f"   [Worker Thread {thread_id}] 🟢 Started processing Batch {batch_id}...")

    # Simulate network latency (OpenAI + Pinecone handshake taking 1.5 to 3 seconds)
    # This would be replaced with our actual logic to post the batch data
    simulated_network_time = random.uniform(1.5, 3.0)
    time.sleep(simulated_network_time)

    # wait for print lock to free up to print to console... 
    with print_lock:
        print(f"   [Worker Thread {thread_id}] ✅ Finished Batch {batch_id} (Took {simulated_network_time:.2f}s). Releasing slot.")
    
    # CRITICAL: Release the token so the main thread knows a slot opened up
    semaphore.release()


def run_simulation():
    print("=" * 70)
    print("🌟 STARTING CONCURRENCY AND THROTTLING SIMULATION")
    print("=" * 70)

    MAX_CONCURRENT_REQUESTS = 3  # Maximum allowed open connections
    TOTAL_BATCHES_TO_PROCESS = 7  # Total mock batches our file reader will find
    
    # Initialize our traffic cop with a max ceiling of 3
    semaphore = threading.BoundedSemaphore(MAX_CONCURRENT_REQUESTS)

    print(f"Setting Max Concurrent Workers to: {MAX_CONCURRENT_REQUESTS}")
    print(f"Simulating a file containing: {TOTAL_BATCHES_TO_PROCESS} total batches\n")
    print("--- Timeline Start ---")

    # Start the background worker thread pool
    ## may want to pass in thread_name_prefix so we can track different errors 
    ## to the same log file and trace it back to specific processes/threads
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        
        # This loop simulates the Main Thread reading the massive JSON file line-by-line
        for batch_id in range(1, TOTAL_BATCHES_TO_PROCESS + 1):
            
            with print_lock:
                print(f"[Main Thread] 🔎 Reading data file... generated Batch {batch_id}.")

            # Check if we are allowed to proceed or if the background pool is full
            # If all 3 tokens are taken, this line freezes the main thread immediately.
            if not semaphore.acquire(blocking=False):
                with print_lock:
                    print(f"⚠️  [Main Thread] !! THK THROTTLE WARNING: All {MAX_CONCURRENT_REQUESTS} worker slots are full!")
                    print(f"   [Main Thread] 🛑 Pausing file reading until a worker finishes...")

                # might make sense to put a wait here?
                
                # Now block for real until a slot opens
                semaphore.acquire(blocking=True)
                with print_lock:
                    print(f"   [Main Thread] 🟢 Resuming! Slot found. Submitting Batch {batch_id}.")

            # Submit the task to an available background worker thread
            # do we want to put this in a try catch block and utilze executor.result()? executor.cancel()? executor.done()?
            executor.submit(mock_api_worker, batch_id, semaphore)
            
            # Simulate the main thread being very fast at reading files (0.2 seconds per batch)
            time.sleep(0.2)

    print("\n" + "=" * 70)
    print("🏁 SIMULATION COMPLETE: All threads returned safely.")
    print("=" * 70)

if __name__ == "__main__":
    run_simulation()