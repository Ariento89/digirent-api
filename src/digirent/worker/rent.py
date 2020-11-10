from digirent.worker.app import app


@app.task
def create_rent_invoice(*args):
    print("Creating rent invoice")
    print(sum(args))
    print("End")
