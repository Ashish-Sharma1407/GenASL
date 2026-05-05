"""
Create a minimal demo dataset for GenASL deployment.
This script generates dummy video clips and pose data for demonstration purposes.
"""

import os
import numpy as np
from pathlib import Path
import json

# Demo signs vocabulary
DEMO_SIGNS = {
    "HELLO": "A greeting sign",
    "THANK": "Expression of gratitude",
    "YOU": "Second person pronoun",
    "GOOD": "Positive adjective",
    "MORNING": "Time of day",
    "NAME": "Noun for personal identity",
    "WHAT": "Question word",
    "YOUR": "Possessive pronoun",
}

def create_demo_structure():
    """Create the demo data directory structure."""
    project_root = Path(__file__).parent.parent
    demo_data = project_root / "demo_data"
    
    dirs = [
        demo_data / "words",
        demo_data / "poses",
        demo_data / "heads",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return demo_data

def create_demo_videos(demo_data_path):
    """Create dummy video files and metadata."""
    words_dir = demo_data_path / "words"
    metadata = {}
    
    for sign_name in DEMO_SIGNS.keys():
        # Create a dummy .npy file (video frames)
        video_file = words_dir / f"{sign_name}.mp4"
        # For demo, just create empty file with .mp4 extension
        video_file.touch()
        
        metadata[sign_name] = {
            "description": DEMO_SIGNS[sign_name],
            "frames": 30,
            "duration": 1.5,
            "file": str(video_file.name)
        }
    
    # Save metadata
    metadata_file = words_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Created {len(DEMO_SIGNS)} demo video clips in {words_dir}")

def create_demo_poses(demo_data_path):
    """Create dummy pose and head data."""
    poses_dir = demo_data_path / "poses"
    heads_dir = demo_data_path / "heads"
    
    for sign_name in DEMO_SIGNS.keys():
        # Create dummy pose numpy array
        # Shape: (num_frames, num_joints, 3) for MediaPipe pose
        pose_data = np.random.rand(30, 33, 3).astype(np.float32)
        pose_file = poses_dir / f"{sign_name}.npy"
        np.save(pose_file, pose_data)
        
        # Create dummy head numpy array
        # Shape: (num_frames, num_face_landmarks, 3) for face landmarks
        head_data = np.random.rand(30, 468, 3).astype(np.float32)
        head_file = heads_dir / f"{sign_name}.npy"
        np.save(head_file, head_data)
    
    print(f"✓ Created {len(DEMO_SIGNS)} demo pose files in {poses_dir}")
    print(f"✓ Created {len(DEMO_SIGNS)} demo head files in {heads_dir}")

def create_readme(demo_data_path):
    """Create README for demo data."""
    readme_content = """# GenASL Demo Dataset

This minimal demo dataset contains dummy ASL sign clips for testing and demonstration purposes.

## Contents

- `words/`: Video clips for each sign (dummy files for demo)
- `poses/`: Pose/skeleton data (.npy files, shape: frames × joints × coordinates)
- `heads/`: Face/head data (.npy files, shape: frames × landmarks × coordinates)

## Signs Included

""" + "\n".join([f"- {sign}: {desc}" for sign, desc in DEMO_SIGNS.items()])

    readme_content += """

## For Production

To use the full ASLLVD dataset:

1. Download from http://asllvd.org/
2. Extract to project root's `asllvd_raw/` folder
3. Run extraction scripts:
   ```
   python extract_all_poses.py
   python extract_all_head.py
   ```

## Notes

- This demo dataset is only for testing GenASL functionality
- For production, use real ASL video data from ASLLVD dataset
- Each sign video should be in MP4 format
- Pose/head data should be in NumPy format (.npy)
"""
    
    readme_file = demo_data_path / "README.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"✓ Created README at {readme_file}")

def main():
    """Main function to create demo dataset."""
    print("Creating GenASL Demo Dataset...")
    print("-" * 50)
    
    demo_data = create_demo_structure()
    create_demo_videos(demo_data)
    create_demo_poses(demo_data)
    create_readme(demo_data)
    
    print("-" * 50)
    print("✓ Demo dataset created successfully!")
    print(f"  Location: {demo_data}")
    print("\nYou can now:")
    print("1. Run: docker-compose up -d")
    print("2. Test backend: curl http://localhost:8000/health")
    print("3. Visit frontend: http://localhost:3000")

if __name__ == "__main__":
    main()
