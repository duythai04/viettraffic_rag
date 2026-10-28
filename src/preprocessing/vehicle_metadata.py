from __future__ import annotations


class VehicleMetadataEnricher:
    DOCUMENT_ID = "168-2024-ND-CP"

    # Mapping verified against parsed article titles.
    ARTICLE_VEHICLE_MAP = {
        "6": "car",
        "7": "motorcycle",
        "8": "specialized_vehicle",
        "9": "bicycle",
        "10": "pedestrian",
    }

    def enrich(self, chunks: list[dict]) -> list[dict]:
        enriched = []

        for chunk in chunks:
            item = chunk.copy()

            article = str(item.get("article", ""))
            document_id = item.get("document_id")

            if document_id == self.DOCUMENT_ID:
                item["vehicle_type"] = (
                    self.ARTICLE_VEHICLE_MAP.get(article)
                )
            else:
                item["vehicle_type"] = None

            enriched.append(item)

        return enriched