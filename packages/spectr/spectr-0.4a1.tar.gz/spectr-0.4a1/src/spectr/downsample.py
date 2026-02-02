import numpy as np
import numpy.typing as npt


def vec_shoelace(left: npt.NDArray, middle: npt.NDArray, right: npt.NDArray):
    """Calculate the areas of triangles between the left point, n-middle points and a right point"""
    assert left.ndim == 1
    assert middle.ndim == 2
    assert right.ndim == 1
    # TODO assert that the x components of the three points are monotonically increasing
    return 0.5 * np.abs(
        left[0] * (middle[:, 1] - right[1])
        + middle[:, 0] * (right[1] - left[1])
        + right[0] * (left[1] - middle[:, 1])
    )


def largest_triangle_three_buckets(
    y, x: npt.NDArray | None = None, *, compression_factor: int
):
    x = x or np.arange(len(y))
    assert x.ndim == 1
    assert y.ndim == 1
    xy = np.vstack((x, y)).T
    bucket_xy = xy[1:-1]
    bucket_view_xy = np.lib.stride_tricks.sliding_window_view(
        bucket_xy, compression_factor, axis=0
    ).reshape((-1, bucket_xy.shape[1], compression_factor))[::compression_factor]

    next_bucket_averages = bucket_view_xy.mean(axis=2)
    selected_points = [xy[0]]
    # TODO: eliminate this loop
    for bucket, next_bucket_avg in zip(
        bucket_view_xy[:-1], next_bucket_averages[1:], strict=True
    ):
        triangle_areas = vec_shoelace(selected_points[-1], bucket.T, next_bucket_avg)
        largest_index = np.argmax(triangle_areas)
        selected_points.append(bucket.T[largest_index])
    selected_points.append(xy[-1])
    return np.asarray(selected_points).T


def maximum_bucket(y, x: npt.NDArray | None = None, *, compression_factor: int):
    x = x or np.arange(len(y))
    assert x.ndim == 1
    assert y.ndim == 1

    y_view = np.lib.stride_tricks.sliding_window_view(y[1:-1], compression_factor)[
        ::compression_factor
    ]
    max_indices = np.argmax(y_view, axis=1)
    flat_index = max_indices + np.arange(len(max_indices)) * compression_factor
    y = np.concatenate(([y[0]], y[flat_index], [y[-1]]))
    x = np.concatenate(([x[0]], x[flat_index], [x[-1]]))
    return x, y
