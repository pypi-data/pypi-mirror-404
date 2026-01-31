

import numpy as np
import json 
import streamlit as st
import matplotlib.pyplot as plt 
from scipy.cluster.vq import kmeans, vq
from scipy.ndimage import gaussian_filter, median_filter
from scipy.optimize import leastsq

def convert_to_serializable(obj):
    """
    Recursively converts NumPy arrays and other non-serializable objects to serializable forms.
    Also converts dictionary keys to standard types (str, int, float).
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert NumPy arrays to lists
    elif isinstance(obj, np.integer):
        return int(obj)  # Convert NumPy integers to Python int
    elif isinstance(obj, np.floating):
        return float(obj)  # Convert NumPy floats to Python float
    elif isinstance(obj, dict):
        return {str(key): convert_to_serializable(value) for key, value in obj.items()}  # Ensure keys are strings
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj  # Base case: return the object itself if it doesn't need conversion

def cluster_analysis_on_searched_images(images, detect_circle_function, n_clusters=3, plot_clusters=False):
    """
    Detects circular pupils in a list of images, performs clustering on their positions and radii
    using scipy's k-means, and returns the cluster assignments for each image.

    Parameters:
        images (list of 2D arrays): List of cropped grayscale images containing single pupils.
        detect_circle_function (function): Function to detect circular pupils (e.g., your detect_circle function).
        n_clusters (int): Number of clusters to use for k-means clustering.
        plot_clusters (bool): If True, displays the clustering results.

    Returns:
        dict: A dictionary with keys:
            - "centers" (list): List of tuples (x, y, radius) for each detected pupil.
            - "clusters" (list): Cluster labels for each image.
            - "centroids" (ndarray): Centroids of the clusters.
    """
    # Step 1: Detect circles in all images
    centers = []
    for idx, image in enumerate(images):
        try:
            center_x, center_y, radius = detect_circle_function(image, plot=False)
            centers.append((center_x, center_y, radius))
        except Exception as e:
            print(f"Warning: Failed to detect circle in image {idx}. Error: {e}")
            centers.append((np.nan, np.nan, np.nan))  # Handle failure gracefully

    # Convert to a numpy array for clustering
    centers_array = np.array([center for center in centers if not np.isnan(center).any()])

    if len(centers_array) < n_clusters:
        raise ValueError("Number of valid centers is less than the number of clusters.")

    # Perform k-means clustering using scipy
    centroids, _ = kmeans(centers_array, n_clusters)
    cluster_labels, _ = vq(centers_array, centroids)

    #  Assign cluster labels back to all images (use NaN for failed detections)
    cluster_assignments = []
    idx_center = 0
    for center in centers:
        if np.isnan(center).any():
            cluster_assignments.append(np.nan)
        else:
            cluster_assignments.append(cluster_labels[idx_center])
            idx_center += 1

    # Plot clustering results (optional)
    if plot_clusters:
        plt.figure(figsize=(8, 6))
        for cluster_id in range(n_clusters):
            cluster_points = centers_array[cluster_labels == cluster_id]
            plt.scatter(cluster_points[:, 0], cluster_points[:, 1], label=f"Cluster {cluster_id}")
        plt.scatter(centroids[:, 0], centroids[:, 1], 
                    color="red", marker="x", s=100, label="Cluster Centers")
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.legend()
        plt.title("Clustering of Detected Pupil Centers")
        plt.show()

    return {
        "centers": centers,
        "clusters": cluster_assignments,
        "centroids": centroids
    }



def plot_aggregate_cluster_images(images, clusters, operation="median"):
    """
    Computes and plots the aggregate (median, mean, or std) image for each cluster.

    Parameters:
        images (list of 2D arrays): List of images corresponding to the data points.
        clusters (list or array): Cluster labels corresponding to each image.
        operation (str): Statistical operation to apply ('median', 'mean', 'std').

    Returns:
        None
    """
    # Validate operation
    valid_operations = {"median", "mean", "std"}
    if operation not in valid_operations:
        raise ValueError(f"Invalid operation. Choose from {valid_operations}.")

    # Convert images to a NumPy array
    images_array = np.array(images)

    # Get unique clusters (exclude NaN)
    unique_clusters = [cluster for cluster in np.unique(clusters) if not np.isnan(cluster)]

    # Prepare the plot
    num_clusters = len(unique_clusters)
    fig, axes = plt.subplots(1, num_clusters, figsize=(6 * num_clusters, 6))
    if num_clusters == 1:
        axes = [axes]  # Ensure axes is iterable for a single cluster

    # Process and plot images for each cluster
    for ax, cluster in zip(axes, unique_clusters):
        # Get indices of images in the current cluster
        cluster_indices = np.where(np.array(clusters) == cluster)[0]

        # Stack the images for the current cluster
        cluster_images = images_array[cluster_indices]

        # Compute the aggregate image
        if operation == "median":
            aggregate_image = np.median(cluster_images, axis=0)
        elif operation == "mean":
            aggregate_image = np.mean(cluster_images, axis=0)
        elif operation == "std":
            aggregate_image = np.std(cluster_images, axis=0)

        # Plot the aggregate image
        im = ax.imshow(aggregate_image, cmap="viridis", origin="lower")
        ax.set_title(f"Cluster {int(cluster)} - {operation.capitalize()} Image")
        fig.colorbar(im, ax=ax, orientation="vertical")

    #plt.tight_layout()
    #plt.show()
    return fig, ax 




def plot_cluster_heatmap(x_positions, y_positions, clusters, show_grid=True, grid_color="white", grid_linewidth=0.5):
    """
    Creates a 2D heatmap of cluster numbers vs x, y positions, with an optional grid overlay.

    Parameters:
        x_positions (list or array): List of x positions.
        y_positions (list or array): List of y positions.
        clusters (list or array): Cluster numbers corresponding to the x, y positions.
        show_grid (bool): If True, overlays a grid on the heatmap.
        grid_color (str): Color of the grid lines (default is 'white').
        grid_linewidth (float): Linewidth of the grid lines (default is 0.5).

    Returns:
        None
    """
    # Convert inputs to NumPy arrays
    x_positions = np.array(x_positions)
    y_positions = np.array(y_positions)
    clusters = np.array(clusters)

    # Ensure inputs have the same length
    if len(x_positions) != len(y_positions) or len(x_positions) != len(clusters):
        raise ValueError("x_positions, y_positions, and clusters must have the same length.")

    # Get unique x and y positions to define the grid
    unique_x = np.unique(x_positions)
    unique_y = np.unique(y_positions)

    # Create an empty grid to store cluster numbers
    heatmap = np.full((len(unique_y), len(unique_x)), np.nan)  # Use NaN for empty cells

    # Map each (x, y) to grid indices
    x_indices = np.searchsorted(unique_x, x_positions)
    y_indices = np.searchsorted(unique_y, y_positions)

    # Fill the heatmap with cluster values
    for x_idx, y_idx, cluster in zip(x_indices, y_indices, clusters):
        heatmap[y_idx, x_idx] = cluster

    # Plot the heatmap
    fig, ax = plt.subplots(figsize=(8, 6))
    cmap = plt.cm.get_cmap('viridis', len(np.unique(clusters)))  # Colormap with distinct colors
    cax = ax.imshow(heatmap, origin='lower', cmap=cmap, extent=[unique_x.min(), unique_x.max(), unique_y.min(), unique_y.max()])

    # Add colorbar
    cbar = fig.colorbar(cax, ax=ax, ticks=np.unique(clusters))
    cbar.set_label('Cluster Number', fontsize=12)

    # Label the axes
    ax.set_xlabel('X Position', fontsize=12)
    ax.set_ylabel('Y Position', fontsize=12)
    ax.set_title('Cluster Heatmap', fontsize=14)

    # Add grid overlay if requested
    if show_grid:
        ax.set_xticks(unique_x, minor=True)
        ax.set_yticks(unique_y, minor=True)
        ax.grid(which="minor", color=grid_color, linestyle="-", linewidth=grid_linewidth)
        ax.tick_params(which="minor", length=0)  # Hide minor tick marks

    plt.tight_layout()

    return fig, ax 




def detect_circle(image, sigma=2, threshold=0.5, plot=True):
    """
    Detects a circular pupil in a cropped image using edge detection and circle fitting.

    Parameters:
        image (2D array): Cropped grayscale image containing a single pupil.
        sigma (float): Standard deviation for Gaussian smoothing.
        threshold (float): Threshold for binarizing edges.
        plot (bool): If True, displays the image with the detected circle overlay.

    Returns:
        tuple: (center_x, center_y, radius) of the detected circle.
    """
    # Normalize the image
    image = image / image.max()

    # Smooth the image to suppress noise
    smoothed_image = gaussian_filter(image, sigma=sigma)

    # Calculate gradients (Sobel-like edge detection)
    grad_x = np.gradient(smoothed_image, axis=1)
    grad_y = np.gradient(smoothed_image, axis=0)
    edges = np.sqrt(grad_x**2 + grad_y**2)

    # Threshold edges to create a binary mask
    binary_edges = edges > (threshold * edges.max())

    # Get edge pixel coordinates
    y, x = np.nonzero(binary_edges)

    # Initial guess for circle parameters
    def initial_guess(x, y):
        center_x, center_y = np.mean(x), np.mean(y)
        radius = np.sqrt(((x - center_x) ** 2 + (y - center_y) ** 2).mean())
        return center_x, center_y, radius

    # Circle model for optimization
    def circle_model(params, x, y):
        center_x, center_y, radius = params
        return np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) - radius

    # Perform least-squares circle fitting
    guess = initial_guess(x, y)
    result, _ = leastsq(circle_model, guess, args=(x, y))
    center_x, center_y, radius = result

    if plot:
        # Create a circular overlay for visualization
        overlay = np.zeros_like(image)
        yy, xx = np.ogrid[: image.shape[0], : image.shape[1]]
        circle_mask = (xx - center_x) ** 2 + (yy - center_y) ** 2 <= radius**2
        overlay[circle_mask] = 1

        # Plot the image and detected circle
        plt.figure(figsize=(6, 6))
        plt.imshow(image, cmap="gray", origin="upper")
        plt.contour(binary_edges, colors="cyan", linewidths=1, label="Edges")
        plt.contour(overlay, colors="red", linewidths=1, label="Detected Circle")
        plt.scatter(center_x, center_y, color="blue", marker="+", label="Center")
        plt.title("Detected Pupil with Circle Overlay")
        plt.legend()
        plt.show()

    return center_x, center_y, radius


xx = np.linspace(0,10,10)
yy = np.linspace(0,10,10)

img_dict = {}
for x in xx:
    for y in yy:
        img_dict[f"({x},{y})"] = np.random.randn(50,50)



data_path = '/Users/bencb/Downloads/'
# save 
json_file_path=data_path + f'delme.json'
with open(json_file_path, "w") as json_file:
    json.dump(convert_to_serializable(img_dict), json_file)

func_list = [np.nanmean, np.median, np.nanstd]
func_label = ['mean', 'median', 'std']


st.title("Frame Signal Analysis")
boundary_threshold = st.text_input( "inside boundary threshold (to help calculate weighted mean of signal)", 0)

for fu, fla in zip(func_list, func_label) :
    if st.button( f"plot {fla} signal vs coord"):

        with open( json_file_path, "r") as file:
            data_dict = json.load(file)  # Parses the JSON content into a Python dictionary

        data_dict_ed = {tuple(map(float, key.strip("()").split(","))): value for key, value in data_dict.items()}

        x_points = np.array( [ float(x) for x,_ in data_dict_ed.keys()] )
        y_points = np.array( [ float(y) for _,y in data_dict_ed.keys()] )

        sss = 200 # point size in scatter 

        user_sig = np.array( [ fu( i ) for i in data_dict.values()] )

        inside_mask = np.ones_like( user_sig ).astype(bool)

        try:
            boundary_threshold = float( boundary_threshold )
        except:
            st.write(f'boundary_threshold={boundary_threshold} cannot be converted to float. Using boundary_threshold=0')
        
        inside_mask = user_sig > boundary_threshold


        # Get x, y coordinates where inside_mask is True
        x_inside = x_points[inside_mask]
        y_inside = y_points[inside_mask]
        weights = user_sig[inside_mask]  # Use mean signal values as weights

        # Compute weighted mean
        x_c = np.sum(x_inside * weights) / np.sum(weights)
        y_c = np.sum(y_inside * weights) / np.sum(weights)

        #st.write(f"initial position {initial_Xpos},{initial_Ypos}")
        
        st.write(f"(signal = {fla}) Weighted Center: ({x_c}, {y_c})")


        if st.button( f"move to this center at ({x_c}, {y_c})"):
            st.write('implement')

        fig, ax = plt.subplots(figsize=(6, 5))
        scatter = ax.scatter(x_points, y_points, c=user_sig, s=sss, cmap='viridis', edgecolors='black', label="Data Points")
        plt.colorbar(scatter, label=f"frame {fla}")
        ax.scatter([x_c],[y_c], color='r', marker='x',label="Weighted Center")
        ax.legend()
        st.pyplot( fig )





# cluster analysis 
st.title("Frame Cluster Analysis")
number_clusters = st.text_input( "number of clusters ", 3)

if st.button( "cluster analysis"):
    with open( json_file_path, "r") as file:
        data_dict = json.load(file)  # Parses the JSON content into a Python dictionary

    data_dict_ed = {tuple(map(float, key.strip("()").split(","))): value for key, value in data_dict.items()}

    x_points = np.array( [ float(x) for x,_ in data_dict_ed.keys()] )
    y_points = np.array( [ float(y) for _,y in data_dict_ed.keys()] )

    image_list = np.array( list( data_dict.values() ) )
    res = cluster_analysis_on_searched_images(images= image_list,
                                            detect_circle_function=detect_circle, 
                                            n_clusters=int(number_clusters), 
                                            plot_clusters=False)




    fig,ax = plot_cluster_heatmap( x_points,  y_points ,  res['clusters'] ) 
    #plt.savefig(args.data_path + f'cluster_search_heatmap_beam{args.beam}.png')
    #plt.close()
    st.pyplot(fig)

    fig,ax = plot_aggregate_cluster_images(images = image_list, clusters = res['clusters'], operation="mean") #std")
    #plt.savefig(args.data_path + f'clusters_heatmap_beam{args.beam}.png')
    st.pyplot(fig)


