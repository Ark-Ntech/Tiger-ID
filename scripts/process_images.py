"""Script to process tiger images and extract embeddings"""

import argparse
import sys
from pathlib import Path
from typing import List
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_db_session, TigerImage
from backend.models.tiger_detection import TigerDetectionModel
from backend.models.tiger_reid import TigerReIDModel
from backend.database.vector_search import store_embedding
from backend.services.tiger_service import TigerService


async def process_image(image_path: Path, tiger_id: str = None):
    """Process a single image"""
    detection_model = TigerDetectionModel()
    reid_model = TigerReIDModel()
    
    # Load models
    await detection_model.load_model()
    await reid_model.load_model()
    
    # Read image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Detect tiger
    detection_result = await detection_model.detect(image_bytes)
    
    if not detection_result.get("detections"):
        print(f"No tiger detected in {image_path}")
        return None
    
    # Extract crop
    tiger_crop = detection_result["detections"][0].get("crop")
    
    if not tiger_crop:
        print(f"Failed to extract tiger crop from {image_path}")
        return None
    
    # Generate embedding
    embedding = await reid_model.generate_embedding(tiger_crop)
    
    # Get bounding box
    bbox = detection_result["detections"][0].get("bbox")
    confidence = detection_result["detections"][0].get("confidence", 0.0)
    
    return {
        "image_path": str(image_path),
        "embedding": embedding,
        "bbox": bbox,
        "confidence": confidence,
        "tiger_id": tiger_id
    }


async def process_directory(image_dir: Path, tiger_id: str = None):
    """Process all images in a directory"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = [f for f in image_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    results = []
    
    for image_file in image_files:
        print(f"Processing {image_file.name}...")
        try:
            result = await process_image(image_file, tiger_id)
            if result:
                results.append(result)
                print(f"✅ Processed {image_file.name}")
            else:
                print(f"⚠️ Skipped {image_file.name}")
        except Exception as e:
            print(f"❌ Error processing {image_file.name}: {str(e)}")
    
    return results


async def save_to_database(results: List[dict], investigation_id: str = None):
    """Save processed images to database"""
    from uuid import uuid4
    
    with get_db_session() as session:
        tiger_service = TigerService(session)
        
        for result in results:
            # Check if tiger exists, or create new
            if result.get("tiger_id"):
                tiger_id = result["tiger_id"]
            else:
                # Create new tiger record
                from backend.database.models import Tiger
                tiger = Tiger(
                    name=f"Tiger from {Path(result['image_path']).stem}",
                    status="unknown"
                )
                session.add(tiger)
                session.commit()
                tiger_id = tiger.tiger_id
            
            # Store image and embedding
            tiger_image = TigerImage(
                tiger_id=tiger_id,
                image_path=result["image_path"],
                detection_bbox=result.get("bbox"),
                detection_confidence=result.get("confidence", 0.0),
                metadata={
                    "processed": True,
                    "investigation_id": investigation_id
                }
            )
            session.add(tiger_image)
            
            # Store embedding
            store_embedding(
                session,
                tiger_id=tiger_id,
                image_id=tiger_image.image_id,
                embedding=result["embedding"]
            )
            
            print(f"✅ Saved image for tiger {tiger_id}")
        
        session.commit()
        print(f"Saved {len(results)} images to database")


def main():
    parser = argparse.ArgumentParser(description='Process tiger images and extract embeddings')
    parser.add_argument('input', type=str, help='Image file or directory')
    parser.add_argument('--tiger-id', type=str, help='Tiger ID to associate with images')
    parser.add_argument('--investigation-id', type=str, help='Investigation ID for metadata')
    parser.add_argument('--save', action='store_true', help='Save to database')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: {args.input} does not exist")
        return
    
    # Process images
    if input_path.is_file():
        print(f"Processing single image: {args.input}")
        results = [asyncio.run(process_image(input_path, args.tiger_id))]
    else:
        print(f"Processing directory: {args.input}")
        results = asyncio.run(process_directory(input_path, args.tiger_id))
    
    if not results:
        print("No images processed")
        return
    
    print(f"Processed {len(results)} images")
    
    # Save to database if requested
    if args.save:
        asyncio.run(save_to_database(results, args.investigation_id))
    
    print("Processing complete!")


if __name__ == "__main__":
    main()

