import os
import json
import random
import shutil

def create_pilot_dataset():
    # Define base paths
    base_dir = "/home/hewanshrestha/Desktop/Hewan/Master_Thesis/nepali-facebook-data-annotation"
    final_dataset_dir = os.path.join(base_dir, "final_dataset")
    output_dir = os.path.join(base_dir, "pilot_data_new")
    output_images_dir = os.path.join(output_dir, "images")

    # Create output directories
    os.makedirs(output_images_dir, exist_ok=True)

    # Define sources
    sources = {
        "codemixed": {
            "jsonl_path": os.path.join(final_dataset_dir, "codemixed", "code_mixed_data.jsonl"),
            "images_path": os.path.join(final_dataset_dir, "codemixed", "images")
        },
        "monolingual": {
            "jsonl_path": os.path.join(final_dataset_dir, "monolingual", "monolingual_data.jsonl"),
            "images_path": os.path.join(final_dataset_dir, "monolingual", "images")
        }
    }

    all_samples = []
    num_samples_per_source = 25

    for source_name, paths in sources.items():
        print(f"Processing {source_name} data...")
        
        # Read data from jsonl file
        with open(paths["jsonl_path"], 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f]
        
        # Get random samples
        samples = random.sample(data, min(num_samples_per_source, len(data)))
        
        # Copy images and add to the list
        for sample in samples:
            image_id = sample.get("image_id")
            if image_id:
                source_image_path = os.path.join(paths["images_path"], image_id)
                dest_image_path = os.path.join(output_images_dir, image_id)
                
                if os.path.exists(source_image_path):
                    shutil.copyfile(source_image_path, dest_image_path)
                else:
                    print(f"Warning: Image not found for {image_id} in {source_name}")
            
            all_samples.append(sample)

    # Save combined data to pilot_data.json
    output_json_path = os.path.join(output_dir, "pilot_data.json")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_samples, f, ensure_ascii=False, indent=4)

    print(f"\nSuccessfully created pilot dataset at {output_dir}")
    print(f"Total items: {len(all_samples)}")
    print(f"Images copied to: {output_images_dir}")

if __name__ == "__main__":
    create_pilot_dataset() 