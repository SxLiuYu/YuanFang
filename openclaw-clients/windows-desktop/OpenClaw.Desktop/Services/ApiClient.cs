using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using RestSharp;

namespace OpenClaw.Desktop.Services
{
    public class ApiClient : IDisposable
    {
        private readonly RestClient _client;
        private readonly string _baseUrl;
        private readonly Dictionary<string, CacheEntry> _cache;
        private readonly SemaphoreSlim _cacheLock;
        private readonly TimeSpan _defaultCacheDuration;
        private string? _authToken;
        private bool _disposed;

        public string? BaseUrl => _baseUrl;
        public string? AuthToken
        {
            get => _authToken;
            set => _authToken = value;
        }

        public event EventHandler<ApiErrorEventArgs>? ErrorOccurred;

        public ApiClient(string baseUrl, TimeSpan? defaultCacheDuration = null)
        {
            _baseUrl = baseUrl ?? throw new ArgumentNullException(nameof(baseUrl));
            _client = new RestClient(baseUrl);
            _cache = new Dictionary<string, CacheEntry>();
            _cacheLock = new SemaphoreSlim(1, 1);
            _defaultCacheDuration = defaultCacheDuration ?? TimeSpan.FromMinutes(5);
        }

        public async Task<T?> GetAsync<T>(string endpoint, Dictionary<string, string>? parameters = null, bool useCache = true, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();
            var cacheKey = BuildCacheKey("GET", endpoint, parameters);

            if (useCache)
            {
                var cached = await GetFromCacheAsync<T>(cacheKey);
                if (cached != null)
                    return cached;
            }

            var request = CreateRequest(endpoint, Method.Get, parameters);

            var response = await ExecuteWithRetryAsync(request, cancellationToken);
            if (!response.IsSuccessful)
            {
                HandleError(response, "GET", endpoint);
                return default;
            }

            var result = DeserializeResponse<T>(response.Content);
            if (result != null && useCache)
            {
                await SetCacheAsync(cacheKey, result);
            }

            return result;
        }

        public async Task<T?> PostAsync<T>(string endpoint, object? data = null, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();
            var request = CreateRequest(endpoint, Method.Post);

            if (data != null)
            {
                request.AddJsonBody(data);
            }

            var response = await ExecuteWithRetryAsync(request, cancellationToken);
            if (!response.IsSuccessful)
            {
                HandleError(response, "POST", endpoint);
                return default;
            }

            return DeserializeResponse<T>(response.Content);
        }

        public async Task<T?> PutAsync<T>(string endpoint, object? data = null, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();
            var request = CreateRequest(endpoint, Method.Put);

            if (data != null)
            {
                request.AddJsonBody(data);
            }

            var response = await ExecuteWithRetryAsync(request, cancellationToken);
            if (!response.IsSuccessful)
            {
                HandleError(response, "PUT", endpoint);
                return default;
            }

            return DeserializeResponse<T>(response.Content);
        }

        public async Task<bool> DeleteAsync(string endpoint, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();
            var request = CreateRequest(endpoint, Method.Delete);

            var response = await ExecuteWithRetryAsync(request, cancellationToken);
            if (!response.IsSuccessful)
            {
                HandleError(response, "DELETE", endpoint);
                return false;
            }

            return true;
        }

        public async Task<T?> DeleteAsync<T>(string endpoint, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();
            var request = CreateRequest(endpoint, Method.Delete);

            var response = await ExecuteWithRetryAsync(request, cancellationToken);
            if (!response.IsSuccessful)
            {
                HandleError(response, "DELETE", endpoint);
                return default;
            }

            return DeserializeResponse<T>(response.Content);
        }

        public async Task<T?> GetHealthDataAsync<T>(string endpoint, CancellationToken cancellationToken = default)
        {
            return await GetAsync<T>(endpoint, null, true, cancellationToken);
        }

        public async Task<T?> GetHealthSummaryAsync<T>(string endpoint, CancellationToken cancellationToken = default)
        {
            return await GetAsync<T>(endpoint, null, false, cancellationToken);
        }

        public async Task<List<Models.HealthData>?> GetHealthDataAsync(DateTime startDate, DateTime endDate)
        {
            var endpoint = $"api/v1/health/data?start={startDate:yyyy-MM-dd}&end={endDate:yyyy-MM-dd}";
            return await GetAsync<List<Models.HealthData>>(endpoint, null, false);
        }

        public async Task<Models.HealthSummary?> GetHealthSummaryAsync(DateTime startDate, DateTime endDate)
        {
            var endpoint = $"api/v1/health/summary?start={startDate:yyyy-MM-dd}&end={endDate:yyyy-MM-dd}";
            return await GetAsync<Models.HealthSummary>(endpoint, null, false);
        }

        public async Task<List<Models.FinanceRecord>?> GetFinanceRecordsAsync(DateTime startDate, DateTime endDate)
        {
            var endpoint = $"api/v1/finance/records?start={startDate:yyyy-MM-dd}&end={endDate:yyyy-MM-dd}";
            return await GetAsync<List<Models.FinanceRecord>>(endpoint, null, false);
        }

        public async Task<Models.FinanceSummary?> GetFinanceSummaryAsync(DateTime startDate, DateTime endDate)
        {
            var endpoint = $"api/v1/finance/summary?start={startDate:yyyy-MM-dd}&end={endDate:yyyy-MM-dd}";
            return await GetAsync<Models.FinanceSummary>(endpoint, null, false);
        }

        public async Task<Stream?> DownloadFileAsync(string endpoint, CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();
            var request = CreateRequest(endpoint, Method.Get);
            var response = await _client.DownloadStreamAsync(request, cancellationToken);

            return response;
        }

        public async Task<bool> TestConnectionAsync()
        {
            ThrowIfDisposed();
            try
            {
                var request = CreateRequest("api/v1/health", Method.Get);
                var response = await _client.ExecuteAsync(request);
                return response.IsSuccessful;
            }
            catch
            {
                return false;
            }
        }

        public async Task<bool> UploadFileAsync(string endpoint, string filePath, string fileParameterName = "file", CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();

            if (!File.Exists(filePath))
                throw new FileNotFoundException("File not found", filePath);

            var request = CreateRequest(endpoint, Method.Post);
            request.AddFile(fileParameterName, filePath);

            var response = await ExecuteWithRetryAsync(request, cancellationToken);
            if (!response.IsSuccessful)
            {
                HandleError(response, "UPLOAD", endpoint);
                return false;
            }

            return true;
        }

        public void SetAuthToken(string token)
        {
            _authToken = token;
        }

        public void ClearAuthToken()
        {
            _authToken = null;
        }

        public async Task ClearCacheAsync()
        {
            await _cacheLock.WaitAsync();
            try
            {
                _cache.Clear();
            }
            finally
            {
                _cacheLock.Release();
            }
        }

        public async Task InvalidateCacheEntryAsync(string endpoint)
        {
            var cacheKey = BuildCacheKey("GET", endpoint, null);
            await _cacheLock.WaitAsync();
            try
            {
                _cache.Remove(cacheKey);
            }
            finally
            {
                _cacheLock.Release();
            }
        }

        private RestRequest CreateRequest(string endpoint, Method method, Dictionary<string, string>? parameters = null)
        {
            var request = new RestRequest(endpoint, method);

            if (!string.IsNullOrEmpty(_authToken))
            {
                request.AddHeader("Authorization", $"Bearer {_authToken}");
            }

            request.AddHeader("Accept", "application/json");
            request.AddHeader("User-Agent", "OpenClaw.Desktop/1.0");

            if (parameters != null)
            {
                foreach (var param in parameters)
                {
                    request.AddQueryParameter(param.Key, param.Value);
                }
            }

            return request;
        }

        private async Task<RestResponse> ExecuteWithRetryAsync(RestRequest request, CancellationToken cancellationToken, int maxRetries = 3)
        {
            var lastException = default(Exception);

            for (int i = 0; i < maxRetries; i++)
            {
                try
                {
                    var response = await _client.ExecuteAsync(request, cancellationToken);

                    if (response.IsSuccessful || response.StatusCode == HttpStatusCode.NotFound || response.StatusCode == HttpStatusCode.BadRequest)
                    {
                        return response;
                    }

                    if (i < maxRetries - 1)
                    {
                        var delay = TimeSpan.FromSeconds(Math.Pow(2, i));
                        await Task.Delay(delay, cancellationToken);
                    }
                }
                catch (Exception ex)
                {
                    lastException = ex;
                    if (i < maxRetries - 1)
                    {
                        var delay = TimeSpan.FromSeconds(Math.Pow(2, i));
                        await Task.Delay(delay, cancellationToken);
                    }
                }
            }

            return new RestResponse
            {
                StatusCode = HttpStatusCode.ServiceUnavailable,
                ErrorMessage = lastException?.Message ?? "Service unavailable",
                ErrorException = lastException
            };
        }

        private T? DeserializeResponse<T>(string? content)
        {
            if (string.IsNullOrWhiteSpace(content))
                return default;

            try
            {
                return JsonConvert.DeserializeObject<T>(content);
            }
            catch (JsonException)
            {
                return default;
            }
        }

        private async Task<T?> GetFromCacheAsync<T>(string cacheKey)
        {
            await _cacheLock.WaitAsync();
            try
            {
                if (_cache.TryGetValue(cacheKey, out var entry))
                {
                    if (entry.Expiration > DateTime.UtcNow)
                    {
                        return (T?)entry.Data;
                    }
                    _cache.Remove(cacheKey);
                }
                return default;
            }
            finally
            {
                _cacheLock.Release();
            }
        }

        private async Task SetCacheAsync<T>(string cacheKey, T data, TimeSpan? duration = null)
        {
            await _cacheLock.WaitAsync();
            try
            {
                var expiration = DateTime.UtcNow.Add(duration ?? _defaultCacheDuration);
                _cache[cacheKey] = new CacheEntry(data, expiration);
            }
            finally
            {
                _cacheLock.Release();
            }
        }

        private string BuildCacheKey(string method, string endpoint, Dictionary<string, string>? parameters)
        {
            var key = $"{method}:{endpoint}";
            if (parameters != null && parameters.Count > 0)
            {
                key += ":" + string.Join(",", parameters.OrderBy(p => p.Key).Select(p => $"{p.Key}={p.Value}"));
            }
            return key;
        }

        private void HandleError(RestResponse response, string method, string endpoint)
        {
            var error = new ApiErrorEventArgs
            {
                Method = method,
                Endpoint = endpoint,
                StatusCode = response.StatusCode,
                Message = response.ErrorMessage ?? response.StatusDescription ?? "Unknown error",
                Exception = response.ErrorException
            };

            ErrorOccurred?.Invoke(this, error);
        }

        private void ThrowIfDisposed()
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(ApiClient));
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _client?.Dispose();
            _cacheLock?.Dispose();
            _disposed = true;
        }

        private class CacheEntry
        {
            public object? Data { get; }
            public DateTime Expiration { get; }

            public CacheEntry(object? data, DateTime expiration)
            {
                Data = data;
                Expiration = expiration;
            }
        }
    }

    public class ApiErrorEventArgs : EventArgs
    {
        public string Method { get; set; } = string.Empty;
        public string Endpoint { get; set; } = string.Empty;
        public HttpStatusCode StatusCode { get; set; }
        public string Message { get; set; } = string.Empty;
        public Exception? Exception { get; set; }
    }
}