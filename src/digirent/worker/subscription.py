from digirent.worker.app import app


@app.task
def create_subscription_invoice(*args):
    print("Creating subscription invoice")
    print(sum(args))
    print("End")
