enum ResourceStatus {
  idle,
  loading,
  success,
  empty,
  error,
  unauthorized,
  offline,
}

class ResourceState<T> {
  const ResourceState({
    this.status = ResourceStatus.idle,
    this.data,
    this.message,
  });
  final ResourceStatus status;
  final T? data;
  final String? message;

  ResourceState<T> copyWith({
    ResourceStatus? status,
    T? data,
    String? message,
  }) => ResourceState<T>(
    status: status ?? this.status,
    data: data ?? this.data,
    message: message ?? this.message,
  );
}
