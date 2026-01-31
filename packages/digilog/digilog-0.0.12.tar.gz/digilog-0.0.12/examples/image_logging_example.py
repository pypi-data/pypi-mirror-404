"""
Example demonstrating image logging with digilog.

This example shows how to log various types of images including:
- PIL Images
- Numpy arrays
- Matplotlib figures
- File paths

Make sure to install image dependencies:
    pip install digilog[image]
    
Or install individually:
    pip install Pillow numpy matplotlib
"""

import digilog
import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import tempfile
import os


def create_sample_pil_image():
    """Create a sample PIL image with some shapes."""
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill='blue', outline='red', width=3)
    draw.ellipse([75, 75, 125, 125], fill='yellow')
    return img


def create_sample_numpy_array():
    """Create a sample numpy array representing an image."""
    # Create a gradient image
    x = np.linspace(0, 1, 256)
    y = np.linspace(0, 1, 256)
    X, Y = np.meshgrid(x, y)
    
    # Create RGB channels
    r = X
    g = Y
    b = 1 - X
    
    # Stack into RGB image
    rgb = np.stack([r, g, b], axis=2)
    return (rgb * 255).astype(np.uint8)


def create_matplotlib_figure():
    """Create a sample matplotlib figure."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Plot 1: Line plot
    x = np.linspace(0, 10, 100)
    ax1.plot(x, np.sin(x), label='sin(x)')
    ax1.plot(x, np.cos(x), label='cos(x)')
    ax1.set_title('Training Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: Scatter plot
    x = np.random.randn(100)
    y = np.random.randn(100)
    ax2.scatter(x, y, alpha=0.5)
    ax2.set_title('Feature Distribution')
    ax2.set_xlabel('Feature 1')
    ax2.set_ylabel('Feature 2')
    ax2.grid(True)
    
    plt.tight_layout()
    return fig


def main():
    """Main example demonstrating various image logging methods."""
    
    # Initialize a run
    print("Initializing digilog run...")
    run = digilog.init(
        project="image-logging-demo",
        name="multi-format-demo",
        config={
            "demo_version": "1.0",
            "image_types": ["pil", "numpy", "matplotlib", "file"]
        }
    )
    
    print("\n=== Example 1: Logging PIL Images ===")
    pil_img = create_sample_pil_image()
    run.log({"pil_shapes": pil_img}, step=0)
    print("✓ Logged PIL image with shapes")
    
    print("\n=== Example 2: Logging Numpy Arrays ===")
    numpy_img = create_sample_numpy_array()
    run.log({"numpy_gradient": numpy_img}, step=1)
    print("✓ Logged numpy array gradient image")
    
    print("\n=== Example 3: Logging Matplotlib Figures ===")
    fig = create_matplotlib_figure()
    run.log({"training_plots": fig}, step=2)
    plt.close(fig)  # Close to free memory
    print("✓ Logged matplotlib figure with multiple plots")
    
    print("\n=== Example 4: Logging from File Path ===")
    # Save a temporary image file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_path = tmp.name
        pil_img.save(temp_path)
    
    try:
        run.log({"file_image": temp_path}, step=3)
        print(f"✓ Logged image from file path: {temp_path}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    print("\n=== Example 5: Using log_image() with Metadata ===")
    run.log_image(
        pil_img,
        name="detailed_shapes",
        step=4,
        title="Geometric Shapes",
        description="A sample image showing rectangle and circle shapes"
    )
    print("✓ Logged image with title and description using log_image()")
    
    print("\n=== Example 6: Mixed Logging (Metrics + Images) ===")
    for step in range(5, 8):
        # Simulate training metrics
        loss = 1.0 / (step + 1)
        accuracy = 0.5 + (step / 20)
        
        # Create a visualization
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(['Loss', 'Accuracy'], [loss, accuracy])
        ax.set_ylim(0, 1)
        ax.set_title(f'Metrics at Step {step}')
        
        # Log everything together
        run.log({
            "loss": loss,
            "accuracy": accuracy,
            "metrics_chart": fig
        }, step=step)
        
        plt.close(fig)
        print(f"✓ Step {step}: Logged metrics (loss={loss:.3f}, acc={accuracy:.3f}) + chart")
    
    print("\n=== Example 7: Logging with Detailed Metadata ===")
    result_img = create_sample_pil_image()
    run.log({
        "final_result": {
            "value": result_img,
            "title": "Final Model Output",
            "description": "Generated output from the trained model after 100 epochs"
        }
    }, step=100)
    print("✓ Logged image with embedded metadata")
    
    # Finish the run
    print("\nFinishing run...")
    run.finish()
    print("✓ Run finished successfully!")
    
    print("\n" + "="*60)
    print("Example completed! Check your digilog dashboard to view the images.")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Set DIGILOG_API_KEY environment variable")
        print("2. Installed image dependencies: pip install digilog[image]")
        print("3. Server is running and accessible")
        raise

