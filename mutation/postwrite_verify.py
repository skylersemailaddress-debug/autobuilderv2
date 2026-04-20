def verify_postwrite(success: bool) -> None:
    if not success:
        raise RuntimeError("Post-write verification failed")
