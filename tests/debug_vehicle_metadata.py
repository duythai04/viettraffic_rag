import json

from src.preprocessing.vehicle_metadata import VehicleMetadataEnricher


def main():
    path = (
        "data/processed/embeddings/"
        "dbc075dd322c83ac.json"
    )

    with open(path, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    enriched = VehicleMetadataEnricher().enrich(chunks)

    vehicle_metadata = {
        chunk["chunk_id"]: chunk["vehicle_type"]
        for chunk in enriched
    }

    print("Total chunks:", len(enriched))
    print("Mapped IDs:", len(vehicle_metadata))

    for article in ["6", "7", "8", "9", "10"]:
        matches = [
            chunk
            for chunk in enriched
            if str(chunk["article"]) == article
        ]

        print("\nArticle:", article)
        print("Chunks:", len(matches))

        if matches:
            first = matches[0]

            print("Document ID:", first["document_id"])
            print("Chunk ID:", first["chunk_id"])
            print("Vehicle:", first["vehicle_type"])

    print("\nChecking traffic-light chunk...")

    matches = [
        chunk
        for chunk in enriched
        if chunk["citation"] == "Điểm c Khoản 7 Điều 7"
    ]

    assert len(matches) == 1, (
        f"Expected exactly one target chunk, found {len(matches)}"
    )

    target = matches[0]

    print("Citation:", target["citation"])
    print("Chunk ID:", target["chunk_id"])
    print("Vehicle:", target["vehicle_type"])

    assert target["vehicle_type"] == "motorcycle"

    print("\nVEHICLE METADATA TEST PASSED")


if __name__ == "__main__":
    main()