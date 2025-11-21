import hashlib, json, datetime


def log_lineage(features, prediction_prob, model_version):
    record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "model_version": model_version,
        "input_hash": hashlib.md5(
            json.dumps(features, sort_keys=True).encode()
        ).hexdigest(),
        "inputs": features,
        "prediction": prediction_prob,
    }
    print("Lineage:", record)
    return record
