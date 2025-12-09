def throttle():
    global request_count, window_start
    request_count += 1
    elapsed = time.time() - window_start
    if request_count >= REQUEST_LIMIT:
        if elapsed < WINDOW_SECONDS:
            sleep_time = WINDOW_SECONDS - elapsed
            print(f"Rate limit reached, sleeping {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        # Reset counter and window
        window_start = time.time()
        request_count = 0