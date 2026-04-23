using System;
using System.Collections.Generic;
using System.Data;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Newtonsoft.Json;

namespace OpenClaw.Desktop.Services
{
    public class DataService : IDisposable
    {
        private readonly string _databasePath;
        private readonly string _connectionString;
        private readonly SemaphoreSlim _connectionLock;
        private readonly ApiClient _apiClient;
        private SqliteConnection? _connection;
        private bool _disposed;
        private bool _isOnline = true;

        public event EventHandler<SyncEventArgs>? SyncStarted;
        public event EventHandler<SyncEventArgs>? SyncCompleted;
        public event EventHandler<DataErrorEventArgs>? ErrorOccurred;
        public event EventHandler<ConnectionStatusEventArgs>? ConnectionStatusChanged;

        public bool IsOnline
        {
            get => _isOnline;
            private set
            {
                if (_isOnline != value)
                {
                    _isOnline = value;
                    ConnectionStatusChanged?.Invoke(this, new ConnectionStatusEventArgs { IsOnline = value });
                }
            }
        }

        public string DatabasePath => _databasePath;

        public DataService(string? databasePath = null, ApiClient? apiClient = null)
        {
            _databasePath = databasePath ?? GetDefaultDatabasePath();
            _connectionString = $"Data Source={_databasePath}";
            _connectionLock = new SemaphoreSlim(1, 1);
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));

            InitializeDatabaseAsync().GetAwaiter().GetResult();
        }

        private static string GetDefaultDatabasePath()
        {
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var appPath = Path.Combine(appDataPath, "OpenClaw", "Desktop");
            Directory.CreateDirectory(appPath);
            return Path.Combine(appPath, "openclaw.db");
        }

        private async Task InitializeDatabaseAsync()
        {
            await _connectionLock.WaitAsync();
            try
            {
                _connection = new SqliteConnection(_connectionString);
                await _connection.OpenAsync();

                await CreateTablesAsync();
                await CreateIndexesAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        private async Task CreateTablesAsync()
        {
            var commands = new[]
            {
                @"CREATE TABLE IF NOT EXISTS Tasks (
                    Id TEXT PRIMARY KEY,
                    Title TEXT NOT NULL,
                    Description TEXT,
                    Status TEXT NOT NULL DEFAULT 'Pending',
                    Priority INTEGER NOT NULL DEFAULT 1,
                    DueDate TEXT,
                    CreatedAt TEXT NOT NULL,
                    UpdatedAt TEXT NOT NULL,
                    CompletedAt TEXT,
                    Tags TEXT,
                    Metadata TEXT,
                    IsSynced INTEGER NOT NULL DEFAULT 0,
                    IsDeleted INTEGER NOT NULL DEFAULT 0
                )",

                @"CREATE TABLE IF NOT EXISTS Notes (
                    Id TEXT PRIMARY KEY,
                    Title TEXT NOT NULL,
                    Content TEXT,
                    Category TEXT,
                    CreatedAt TEXT NOT NULL,
                    UpdatedAt TEXT NOT NULL,
                    IsSynced INTEGER NOT NULL DEFAULT 0,
                    IsDeleted INTEGER NOT NULL DEFAULT 0
                )",

                @"CREATE TABLE IF NOT EXISTS SyncQueue (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Entity TEXT NOT NULL,
                    EntityId TEXT NOT NULL,
                    Operation TEXT NOT NULL,
                    Timestamp TEXT NOT NULL,
                    RetryCount INTEGER NOT NULL DEFAULT 0
                )",

                @"CREATE TABLE IF NOT EXISTS Settings (
                    Key TEXT PRIMARY KEY,
                    Value TEXT,
                    UpdatedAt TEXT NOT NULL
                )",

                @"CREATE TABLE IF NOT EXISTS Cache (
                    Key TEXT PRIMARY KEY,
                    Value TEXT,
                    Expiration TEXT NOT NULL
                )"
            };

            foreach (var command in commands)
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = command;
                await cmd.ExecuteNonQueryAsync();
            }
        }

        private async Task CreateIndexesAsync()
        {
            var indexes = new[]
            {
                "CREATE INDEX IF NOT EXISTS IX_Tasks_Status ON Tasks(Status)",
                "CREATE INDEX IF NOT EXISTS IX_Tasks_DueDate ON Tasks(DueDate)",
                "CREATE INDEX IF NOT EXISTS IX_Tasks_IsSynced ON Tasks(IsSynced)",
                "CREATE INDEX IF NOT EXISTS IX_Notes_Category ON Notes(Category)",
                "CREATE INDEX IF NOT EXISTS IX_SyncQueue_Timestamp ON SyncQueue(Timestamp)",
                "CREATE INDEX IF NOT EXISTS IX_Cache_Expiration ON Cache(Expiration)"
            };

            foreach (var index in indexes)
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = index;
                await cmd.ExecuteNonQueryAsync();
            }
        }

        public async Task<T?> GetSettingAsync<T>(string key, T? defaultValue = default)
        {
            ThrowIfDisposed();

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = "SELECT Value FROM Settings WHERE Key = @key";
                cmd.Parameters.AddWithValue("@key", key);

                var result = await cmd.ExecuteScalarAsync();
                if (result == null || result == DBNull.Value)
                    return defaultValue;

                var jsonValue = result.ToString();
                if (string.IsNullOrEmpty(jsonValue))
                    return defaultValue;

                try
                {
                    return JsonConvert.DeserializeObject<T>(jsonValue);
                }
                catch
                {
                    return defaultValue;
                }
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task SetSettingAsync<T>(string key, T value)
        {
            ThrowIfDisposed();

            var jsonValue = JsonConvert.SerializeObject(value);
            var timestamp = DateTime.UtcNow.ToString("O");

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = @"
                    INSERT OR REPLACE INTO Settings (Key, Value, UpdatedAt)
                    VALUES (@key, @value, @timestamp)";
                cmd.Parameters.AddWithValue("@key", key);
                cmd.Parameters.AddWithValue("@value", jsonValue);
                cmd.Parameters.AddWithValue("@timestamp", timestamp);

                await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task<IEnumerable<T>> QueryAsync<T>(string tableName, string? whereClause = null, Dictionary<string, object>? parameters = null)
        {
            ThrowIfDisposed();

            var results = new List<T>();
            var sql = $"SELECT * FROM {tableName}";

            if (!string.IsNullOrEmpty(whereClause))
            {
                sql += $" WHERE {whereClause}";
            }

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;

                if (parameters != null)
                {
                    foreach (var param in parameters)
                    {
                        cmd.Parameters.AddWithValue($"@{param.Key}", param.Value);
                    }
                }

                using var reader = await cmd.ExecuteReaderAsync();
                while (await reader.ReadAsync())
                {
                    var item = MapReaderToObject<T>(reader);
                    if (item != null)
                        results.Add(item);
                }
            }
            finally
            {
                _connectionLock.Release();
            }

            return results;
        }

        public async Task<int> ExecuteAsync(string sql, Dictionary<string, object>? parameters = null)
        {
            ThrowIfDisposed();

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;

                if (parameters != null)
                {
                    foreach (var param in parameters)
                    {
                        cmd.Parameters.AddWithValue($"@{param.Key}", param.Value);
                    }
                }

                return await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task<T?> QueryScalarAsync<T>(string sql, Dictionary<string, object>? parameters = null)
        {
            ThrowIfDisposed();

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;

                if (parameters != null)
                {
                    foreach (var param in parameters)
                    {
                        cmd.Parameters.AddWithValue($"@{param.Key}", param.Value);
                    }
                }

                var result = await cmd.ExecuteScalarAsync();
                if (result == null || result == DBNull.Value)
                    return default;

                return (T?)Convert.ChangeType(result, typeof(T));
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task<int> InsertAsync(string tableName, Dictionary<string, object> values)
        {
            ThrowIfDisposed();

            var columns = string.Join(", ", values.Keys);
            var parameters = string.Join(", ", values.Keys.Select(k => $"@{k}"));

            var sql = $"INSERT INTO {tableName} ({columns}) VALUES ({parameters}); SELECT last_insert_rowid();";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;

                foreach (var param in values)
                {
                    cmd.Parameters.AddWithValue($"@{param.Key}", param.Value ?? DBNull.Value);
                }

                var result = await cmd.ExecuteScalarAsync();
                return Convert.ToInt32(result);
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task<int> UpdateAsync(string tableName, Dictionary<string, object> values, string whereClause, Dictionary<string, object>? whereParameters = null)
        {
            ThrowIfDisposed();

            var setClause = string.Join(", ", values.Keys.Select(k => $"{k} = @{k}"));
            var sql = $"UPDATE {tableName} SET {setClause} WHERE {whereClause}";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;

                foreach (var param in values)
                {
                    cmd.Parameters.AddWithValue($"@{param.Key}", param.Value ?? DBNull.Value);
                }

                if (whereParameters != null)
                {
                    foreach (var param in whereParameters)
                    {
                        cmd.Parameters.AddWithValue($"@wp_{param.Key}", param.Value);
                    }
                }

                return await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task<int> DeleteAsync(string tableName, string whereClause, Dictionary<string, object>? parameters = null)
        {
            ThrowIfDisposed();

            var sql = $"DELETE FROM {tableName} WHERE {whereClause}";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;

                if (parameters != null)
                {
                    foreach (var param in parameters)
                    {
                        cmd.Parameters.AddWithValue($"@{param.Key}", param.Value);
                    }
                }

                return await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task<bool> SyncDataAsync(CancellationToken cancellationToken = default)
        {
            ThrowIfDisposed();

            SyncStarted?.Invoke(this, new SyncEventArgs { Timestamp = DateTime.UtcNow });

            try
            {
                IsOnline = await CheckConnectivityAsync(cancellationToken);

                if (!IsOnline)
                {
                    SyncCompleted?.Invoke(this, new SyncEventArgs { Timestamp = DateTime.UtcNow, Success = false, Message = "Offline mode" });
                    return false;
                }

                var pendingChanges = await GetPendingSyncItemsAsync(cancellationToken);
                var success = true;

                foreach (var item in pendingChanges)
                {
                    cancellationToken.ThrowIfCancellationRequested();

                    try
                    {
                        var syncResult = await SyncItemAsync(item, cancellationToken);
                        if (syncResult)
                        {
                            await MarkAsSyncedAsync(item);
                        }
                        else
                        {
                            success = false;
                        }
                    }
                    catch (Exception ex)
                    {
                        await IncrementRetryCountAsync(item.Id);
                        ErrorOccurred?.Invoke(this, new DataErrorEventArgs
                        {
                            Operation = "Sync",
                            Message = $"Failed to sync {item.Entity}:{item.EntityId}",
                            Exception = ex
                        });
                        success = false;
                    }
                }

                await CleanExpiredCacheAsync();

                SyncCompleted?.Invoke(this, new SyncEventArgs
                {
                    Timestamp = DateTime.UtcNow,
                    Success = success,
                    Message = success ? "Sync completed" : "Sync completed with errors"
                });

                return success;
            }
            catch (Exception ex)
            {
                ErrorOccurred?.Invoke(this, new DataErrorEventArgs
                {
                    Operation = "Sync",
                    Message = "Sync failed",
                    Exception = ex
                });

                SyncCompleted?.Invoke(this, new SyncEventArgs
                {
                    Timestamp = DateTime.UtcNow,
                    Success = false,
                    Message = ex.Message
                });

                return false;
            }
        }

        private async Task<bool> CheckConnectivityAsync(CancellationToken cancellationToken)
        {
            try
            {
                var result = await _apiClient.GetAsync<object>("health", cancellationToken: cancellationToken);
                return result != null;
            }
            catch
            {
                return false;
            }
        }

        private async Task<List<SyncQueueItem>> GetPendingSyncItemsAsync(CancellationToken cancellationToken)
        {
            var sql = "SELECT * FROM SyncQueue ORDER BY Timestamp ASC";
            var items = new List<SyncQueueItem>();

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;

                using var reader = await cmd.ExecuteReaderAsync();
                while (await reader.ReadAsync())
                {
                    items.Add(new SyncQueueItem
                    {
                        Id = reader.GetInt32(0),
                        Entity = reader.GetString(1),
                        EntityId = reader.GetString(2),
                        Operation = reader.GetString(3),
                        Timestamp = DateTime.Parse(reader.GetString(4)),
                        RetryCount = reader.GetInt32(5)
                    });
                }
            }
            finally
            {
                _connectionLock.Release();
            }

            return items;
        }

        private async Task<bool> SyncItemAsync(SyncQueueItem item, CancellationToken cancellationToken)
        {
            var entityData = await GetEntityDataAsync(item.Entity, item.EntityId);
            if (entityData == null)
                return false;

            var endpoint = $"api/{item.Entity.ToLower()}";

            try
            {
                switch (item.Operation.ToLower())
                {
                    case "create":
                    case "update":
                        var result = await _apiClient.PutAsync<object>($"{endpoint}/{item.EntityId}", entityData, cancellationToken);
                        return result != null;

                    case "delete":
                        return await _apiClient.DeleteAsync($"{endpoint}/{item.EntityId}", cancellationToken);

                    default:
                        return false;
                }
            }
            catch
            {
                return false;
            }
        }

        private async Task<Dictionary<string, object>?> GetEntityDataAsync(string entity, string entityId)
        {
            var sql = $"SELECT * FROM {entity} WHERE Id = @id";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;
                cmd.Parameters.AddWithValue("@id", entityId);

                using var reader = await cmd.ExecuteReaderAsync();
                if (await reader.ReadAsync())
                {
                    var data = new Dictionary<string, object>();
                    for (int i = 0; i < reader.FieldCount; i++)
                    {
                        data[reader.GetName(i)] = reader.IsDBNull(i) ? null! : reader.GetValue(i);
                    }
                    return data;
                }

                return null;
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        private async Task MarkAsSyncedAsync(SyncQueueItem item)
        {
            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = "DELETE FROM SyncQueue WHERE Id = @id";
                cmd.Parameters.AddWithValue("@id", item.Id);
                await cmd.ExecuteNonQueryAsync();

                cmd.CommandText = $"UPDATE {item.Entity} SET IsSynced = 1 WHERE Id = @entityId";
                cmd.Parameters.Clear();
                cmd.Parameters.AddWithValue("@entityId", item.EntityId);
                await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        private async Task IncrementRetryCountAsync(int syncQueueId)
        {
            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = "UPDATE SyncQueue SET RetryCount = RetryCount + 1 WHERE Id = @id";
                cmd.Parameters.AddWithValue("@id", syncQueueId);
                await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task AddToSyncQueueAsync(string entity, string entityId, string operation)
        {
            var sql = @"
                INSERT INTO SyncQueue (Entity, EntityId, Operation, Timestamp)
                VALUES (@entity, @entityId, @operation, @timestamp)";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;
                cmd.Parameters.AddWithValue("@entity", entity);
                cmd.Parameters.AddWithValue("@entityId", entityId);
                cmd.Parameters.AddWithValue("@operation", operation);
                cmd.Parameters.AddWithValue("@timestamp", DateTime.UtcNow.ToString("O"));

                await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task<T?> GetCachedAsync<T>(string key)
        {
            var sql = "SELECT Value, Expiration FROM Cache WHERE Key = @key";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;
                cmd.Parameters.AddWithValue("@key", key);

                using var reader = await cmd.ExecuteReaderAsync();
                if (await reader.ReadAsync())
                {
                    var expiration = DateTime.Parse(reader.GetString(1));
                    if (expiration > DateTime.UtcNow)
                    {
                        var json = reader.GetString(0);
                        return JsonConvert.DeserializeObject<T>(json);
                    }
                }

                return default;
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task SetCacheAsync<T>(string key, T value, TimeSpan? expiration = null)
        {
            var json = JsonConvert.SerializeObject(value);
            var expirationTime = DateTime.UtcNow.Add(expiration ?? TimeSpan.FromHours(1));

            var sql = @"
                INSERT OR REPLACE INTO Cache (Key, Value, Expiration)
                VALUES (@key, @value, @expiration)";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;
                cmd.Parameters.AddWithValue("@key", key);
                cmd.Parameters.AddWithValue("@value", json);
                cmd.Parameters.AddWithValue("@expiration", expirationTime.ToString("O"));

                await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        private async Task CleanExpiredCacheAsync()
        {
            var sql = "DELETE FROM Cache WHERE Expiration < @now";

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = sql;
                cmd.Parameters.AddWithValue("@now", DateTime.UtcNow.ToString("O"));
                await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        private static T? MapReaderToObject<T>(IDataRecord reader)
        {
            try
            {
                var type = typeof(T);
                var instance = Activator.CreateInstance<T>();

                if (instance == null)
                    return default;

                var properties = type.GetProperties();

                foreach (var property in properties)
                {
                    if (!property.CanWrite)
                        continue;

                    var ordinal = reader.GetOrdinal(property.Name);
                    if (ordinal < 0)
                        continue;

                    if (reader.IsDBNull(ordinal))
                    {
                        property.SetValue(instance, null);
                        continue;
                    }

                    var value = reader.GetValue(ordinal);

                    if (property.PropertyType == typeof(string))
                    {
                        property.SetValue(instance, value.ToString());
                    }
                    else if (property.PropertyType == typeof(int))
                    {
                        property.SetValue(instance, Convert.ToInt32(value));
                    }
                    else if (property.PropertyType == typeof(long))
                    {
                        property.SetValue(instance, Convert.ToInt64(value));
                    }
                    else if (property.PropertyType == typeof(double))
                    {
                        property.SetValue(instance, Convert.ToDouble(value));
                    }
                    else if (property.PropertyType == typeof(bool))
                    {
                        property.SetValue(instance, Convert.ToBoolean(value));
                    }
                    else if (property.PropertyType == typeof(DateTime))
                    {
                        property.SetValue(instance, DateTime.Parse(value.ToString()));
                    }
                    else if (property.PropertyType == typeof(DateTime?))
                    {
                        property.SetValue(instance, DateTime.Parse(value.ToString()));
                    }
                    else
                    {
                        property.SetValue(instance, value);
                    }
                }

                return instance;
            }
            catch
            {
                return default;
            }
        }

        private void ThrowIfDisposed()
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(DataService));
        }

        public async Task VacuumAsync()
        {
            ThrowIfDisposed();

            await _connectionLock.WaitAsync();
            try
            {
                using var cmd = _connection!.CreateCommand();
                cmd.CommandText = "VACUUM";
                await cmd.ExecuteNonQueryAsync();
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public async Task BackupAsync(string backupPath)
        {
            ThrowIfDisposed();

            await _connectionLock.WaitAsync();
            try
            {
                File.Copy(_databasePath, backupPath, overwrite: true);
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _connectionLock.Wait();
            try
            {
                _connection?.Close();
                _connection?.Dispose();
            }
            finally
            {
                _connectionLock.Release();
                _connectionLock.Dispose();
            }

            _disposed = true;
        }
    }

    public class SyncQueueItem
    {
        public int Id { get; set; }
        public string Entity { get; set; } = string.Empty;
        public string EntityId { get; set; } = string.Empty;
        public string Operation { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public int RetryCount { get; set; }
    }

    public class SyncEventArgs : EventArgs
    {
        public DateTime Timestamp { get; set; }
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
    }

    public class DataErrorEventArgs : EventArgs
    {
        public string Operation { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public Exception? Exception { get; set; }
    }

    public class ConnectionStatusEventArgs : EventArgs
    {
        public bool IsOnline { get; set; }
    }
}