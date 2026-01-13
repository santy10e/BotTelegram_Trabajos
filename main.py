from fetchers import computrabajo, multitrabajos, indeed, remote
from db import init_db, save_job_if_new
from notifier import notify
import time

FETCHERS = [
    computrabajo.fetch,
    multitrabajos.fetch,
    indeed.fetch,
    #remote.fetch
]

def main():
    init_db()
    while True:
        for fetch in FETCHERS:
            try:
                jobs = fetch()
                for job in jobs:
                    if save_job_if_new(job):
                        notify(job)  # SOLO LAS NUEVAS
            except Exception as e:
                print("Fetcher error:", e)

        time.sleep(1800)  # 30 min

if __name__ == "__main__":
    main()