from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

collection = "viettraffic_legal"

offset = None
matches = []

keywords = [
    "đèn tín hiệu giao thông",
    "tín hiệu đèn giao thông",
    "không chấp hành hiệu lệnh",
]

while True:
    points, offset = client.scroll(
        collection_name=collection,
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False,
    )

    for point in points:
        payload = point.payload or {}

        text = (
            str(payload.get("content") or "")
            + "\n"
            + str(payload.get("embedding_text") or "")
        ).lower()

        if any(keyword in text for keyword in keywords):
            matches.append(payload)

    if offset is None:
        break

print(f"Found {len(matches)} matching chunks")

for item in matches:
    print("=" * 70)
    print("Citation:", item.get("citation"))
    print("Article:", item.get("article"))
    print("Clause:", item.get("clause"))
    print("Point:", item.get("point"))
    print("Preamble:", item.get("clause_preamble"))
    print("Content:", item.get("content"))