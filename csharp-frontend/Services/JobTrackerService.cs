using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.JSInterop;
using csharp_frontend.Models;

namespace csharp_frontend.Services
{
    public class JobTrackerService
    {
        private readonly HttpClient _http;
        private readonly IJSRuntime _js;
        private readonly string _apiBaseUrl;

        public JobTrackerService(HttpClient http, IJSRuntime js)
        {
            _http = http;
            _js = js;
            
            // Dynamically resolve backend endpoint
            _apiBaseUrl = "https://thatos-jobtracker-api.onrender.com"; // Default remote endpoint
            var baseAddress = _http.BaseAddress?.ToString() ?? "";
            if (baseAddress.Contains("localhost") || baseAddress.Contains("127.0.0.1"))
            {
                _apiBaseUrl = "http://localhost:8085"; // Local fallback
            }
        }

        // --- Authentication & Session Management ---

        public async Task<bool> IsLoggedInAsync()
        {
            var token = await GetTokenAsync();
            return !string.IsNullOrEmpty(token);
        }

        public async Task<string?> GetUsernameAsync()
        {
            return await _js.InvokeAsync<string?>("localStorage.getItem", "username");
        }

        public async Task<string?> GetTokenAsync()
        {
            return await _js.InvokeAsync<string?>("localStorage.getItem", "jwt_token");
        }

        public async Task<bool> RegisterAsync(string username, string password)
        {
            var response = await _http.PostAsJsonAsync($"{_apiBaseUrl}/api/auth/register", new RegisterModel { Username = username, Password = password });
            return response.IsSuccessStatusCode;
        }

        public async Task<bool> LoginAsync(string username, string password)
        {
            var response = await _http.PostAsJsonAsync($"{_apiBaseUrl}/api/auth/login", new LoginModel { Username = username, Password = password });
            if (response.IsSuccessStatusCode)
            {
                var tokenData = await response.Content.ReadFromJsonAsync<TokenResponse>();
                if (tokenData != null)
                {
                    await _js.InvokeVoidAsync("localStorage.setItem", "jwt_token", tokenData.Token);
                    await _js.InvokeVoidAsync("localStorage.setItem", "username", tokenData.Username);
                    return true;
                }
            }
            return false;
        }

        public async Task LogoutAsync()
        {
            await _js.InvokeVoidAsync("localStorage.removeItem", "jwt_token");
            await _js.InvokeVoidAsync("localStorage.removeItem", "username");
        }

        // --- HTTP Helper for Authenticated Requests ---

        private async Task<HttpRequestMessage> CreateRequestAsync(HttpMethod method, string path, object? content = null)
        {
            var request = new HttpRequestMessage(method, $"{_apiBaseUrl}{path}");
            var token = await GetTokenAsync();
            if (!string.IsNullOrEmpty(token))
            {
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            }
            if (content != null)
            {
                request.Content = JsonContent.Create(content);
            }
            return request;
        }

        private async Task<T?> SendAsync<T>(HttpMethod method, string path, object? content = null)
        {
            var request = await CreateRequestAsync(method, path, content);
            var response = await _http.SendAsync(request);
            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            {
                await LogoutAsync();
                return default;
            }
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<T>();
        }

        private async Task<bool> SendVoidAsync(HttpMethod method, string path, object? content = null)
        {
            var request = await CreateRequestAsync(method, path, content);
            var response = await _http.SendAsync(request);
            if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
            {
                await LogoutAsync();
                return false;
            }
            return response.IsSuccessStatusCode;
        }

        // --- Jobs Resources ---

        public async Task<PaginatedResponse<Job>?> GetJobsAsync(
            string? title = null, 
            string? company = null, 
            string? skills = null, 
            bool? visaSponsorship = null,
            int? maxExperience = null,
            string? sourcePlatform = null,
            int page = 0, 
            int size = 10)
        {
            var queryParams = new List<string>();
            if (!string.IsNullOrEmpty(title)) queryParams.Add($"title={Uri.EscapeDataString(title)}");
            if (!string.IsNullOrEmpty(company)) queryParams.Add($"company={Uri.EscapeDataString(company)}");
            if (!string.IsNullOrEmpty(skills)) queryParams.Add($"skills={Uri.EscapeDataString(skills)}");
            if (visaSponsorship.HasValue) queryParams.Add($"visaSponsorship={visaSponsorship.Value.ToString().ToLower()}");
            if (maxExperience.HasValue) queryParams.Add($"maxExperience={maxExperience.Value}");
            if (!string.IsNullOrEmpty(sourcePlatform)) queryParams.Add($"sourcePlatform={Uri.EscapeDataString(sourcePlatform)}");
            queryParams.Add($"page={page}");
            queryParams.Add($"size={size}");

            var queryString = string.Join("&", queryParams);
            return await SendAsync<PaginatedResponse<Job>>(HttpMethod.Get, $"/api/jobs?{queryString}");
        }

        // --- Applications Resources ---

        public async Task<List<Application>> GetApplicationsAsync()
        {
            var apps = await SendAsync<List<Application>>(HttpMethod.Get, "/api/applications");
            return apps ?? new List<Application>();
        }

        public async Task<Application?> GetApplicationByIdAsync(long id)
        {
            return await SendAsync<Application>(HttpMethod.Get, $"/api/applications/{id}");
        }

        public async Task<Application?> CreateApplicationAsync(long jobId, string status = "Saved", string? dateApplied = null, string? cvFilePath = null)
        {
            var request = new CreateApplicationRequest
            {
                JobId = jobId,
                Status = status,
                DateApplied = dateApplied ?? string.Empty,
                CvFilePath = cvFilePath ?? string.Empty
            };
            return await SendAsync<Application>(HttpMethod.Post, "/api/applications", request);
        }

        public async Task<Application?> UpdateApplicationStatusAsync(long id, string status)
        {
            return await SendAsync<Application>(HttpMethod.Put, $"/api/applications/{id}/status", new UpdateStatusRequest { Status = status });
        }

        public async Task<Application?> UpdateApplicationCvPathAsync(long id, string cvFilePath)
        {
            return await SendAsync<Application>(HttpMethod.Put, $"/api/applications/{id}/cv", new UpdateCvRequest { CvFilePath = cvFilePath });
        }

        public async Task<bool> DeleteApplicationAsync(long id)
        {
            return await SendVoidAsync(HttpMethod.Delete, $"/api/applications/{id}");
        }

        // --- Notes Resources ---

        public async Task<Note?> AddNoteAsync(long applicationId, string content)
        {
            return await SendAsync<Note>(HttpMethod.Post, $"/api/applications/{applicationId}/notes", new CreateNoteRequest { Content = content });
        }

        public async Task<bool> DeleteNoteAsync(long noteId)
        {
            return await SendVoidAsync(HttpMethod.Delete, $"/api/applications/notes/{noteId}");
        }

        // --- Contacts Resources ---

        public async Task<Contact?> AddContactAsync(long applicationId, string name, string role, string email, string phone)
        {
            var request = new CreateContactRequest { Name = name, Role = role, Email = email, Phone = phone };
            return await SendAsync<Contact>(HttpMethod.Post, $"/api/applications/{applicationId}/contacts", request);
        }

        public async Task<bool> DeleteContactAsync(long contactId)
        {
            return await SendVoidAsync(HttpMethod.Delete, $"/api/applications/contacts/{contactId}");
        }

        // --- Dashboard / Analytics ---

        public async Task<DashboardStats?> GetDashboardStatsAsync()
        {
            return await SendAsync<DashboardStats>(HttpMethod.Get, "/api/dashboard/stats");
        }
    }
}
