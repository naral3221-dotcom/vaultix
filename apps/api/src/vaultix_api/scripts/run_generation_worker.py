from vaultix_api.db.session import get_sessionmaker
from vaultix_api.services.generation_worker import process_next_generation_request


def main() -> None:
    maker = get_sessionmaker()
    with maker() as session:
        request = process_next_generation_request(session)
        if request is None:
            print("No queued generation requests.")
            return
        print(f"Processed generation request #{request.id} -> asset #{request.result_asset_id}.")


if __name__ == "__main__":
    main()
