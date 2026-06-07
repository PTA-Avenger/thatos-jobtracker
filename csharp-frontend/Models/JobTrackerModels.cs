using System.Text.Json.Serialization;

namespace csharp_frontend.Models
{
    public class LoginModel
    {
        [JsonPropertyName("username")]
        public string Username { get; set; } = string.Empty;

        [JsonPropertyName("password")]
        public string Password { get; set; } = string.Empty;
    }

    public class RegisterModel
    {
        [JsonPropertyName("username")]
        public string Username { get; set; } = string.Empty;

        [JsonPropertyName("password")]
        public string Password { get; set; } = string.Empty;
    }

    public class TokenResponse
    {
        [JsonPropertyName("token")]
        public string Token { get; set; } = string.Empty;

        [JsonPropertyName("username")]
        public string Username { get; set; } = string.Empty;
    }

    public class Job
    {
        [JsonPropertyName("id")]
        public long Id { get; set; }

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("company")]
        public string Company { get; set; } = string.Empty;

        [JsonPropertyName("location")]
        public string Location { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("skills")]
        public string Skills { get; set; } = string.Empty; // Comma-separated list of skills

        [JsonPropertyName("url")]
        public string Url { get; set; } = string.Empty;

        [JsonPropertyName("datePosted")]
        public string DatePosted { get; set; } = string.Empty;

        [JsonPropertyName("dateScraped")]
        public string DateScraped { get; set; } = string.Empty;

        [JsonPropertyName("jobHash")]
        public string JobHash { get; set; } = string.Empty;

        [JsonPropertyName("closingDate")]
        public string ClosingDate { get; set; } = string.Empty;

        [JsonPropertyName("visaSponsorship")]
        public bool? VisaSponsorship { get; set; }

        [JsonPropertyName("yearsExperienceRequired")]
        public int? YearsExperienceRequired { get; set; }

        [JsonPropertyName("snapshotPath")]
        public string SnapshotPath { get; set; } = string.Empty;

        [JsonPropertyName("sourcePlatform")]
        public string SourcePlatform { get; set; } = string.Empty;

        [JsonPropertyName("isGhostJob")]
        public bool IsGhostJob { get; set; }
    }

    public class Application
    {
        [JsonPropertyName("id")]
        public long Id { get; set; }

        [JsonPropertyName("job")]
        public Job Job { get; set; } = new();

        [JsonPropertyName("status")]
        public string Status { get; set; } = "Saved"; // Saved, Applied, Interview, Offer, Rejected

        [JsonPropertyName("dateApplied")]
        public string DateApplied { get; set; } = string.Empty;

        [JsonPropertyName("cvFilePath")]
        public string CvFilePath { get; set; } = string.Empty;

        [JsonPropertyName("notes")]
        public List<Note> Notes { get; set; } = new();

        [JsonPropertyName("contacts")]
        public List<Contact> Contacts { get; set; } = new();
    }

    public class Note
    {
        [JsonPropertyName("id")]
        public long Id { get; set; }

        [JsonPropertyName("content")]
        public string Content { get; set; } = string.Empty;

        [JsonPropertyName("dateCreated")]
        public string DateCreated { get; set; } = string.Empty;
    }

    public class Contact
    {
        [JsonPropertyName("id")]
        public long Id { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("role")]
        public string Role { get; set; } = string.Empty;

        [JsonPropertyName("email")]
        public string Email { get; set; } = string.Empty;

        [JsonPropertyName("phone")]
        public string Phone { get; set; } = string.Empty;
    }

    public class DashboardStats
    {
        [JsonPropertyName("totalApplications")]
        public long TotalApplications { get; set; }

        [JsonPropertyName("statusDistribution")]
        public Dictionary<string, long> StatusDistribution { get; set; } = new();

        [JsonPropertyName("applicationTimeline")]
        public Dictionary<string, long> ApplicationTimeline { get; set; } = new();
    }

    public class CreateApplicationRequest
    {
        [JsonPropertyName("jobId")]
        public long JobId { get; set; }

        [JsonPropertyName("status")]
        public string Status { get; set; } = "Saved";

        [JsonPropertyName("dateApplied")]
        public string DateApplied { get; set; } = string.Empty;

        [JsonPropertyName("cvFilePath")]
        public string CvFilePath { get; set; } = string.Empty;
    }

    public class UpdateStatusRequest
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;
    }

    public class UpdateCvRequest
    {
        [JsonPropertyName("cvFilePath")]
        public string CvFilePath { get; set; } = string.Empty;
    }

    public class CreateNoteRequest
    {
        [JsonPropertyName("content")]
        public string Content { get; set; } = string.Empty;
    }

    public class CreateContactRequest
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("role")]
        public string Role { get; set; } = string.Empty;

        [JsonPropertyName("email")]
        public string Email { get; set; } = string.Empty;

        [JsonPropertyName("phone")]
        public string Phone { get; set; } = string.Empty;
    }

    // Generic API wrapper for paginated jobs list
    public class PaginatedResponse<T>
    {
        [JsonPropertyName("content")]
        public List<T> Content { get; set; } = new();

        [JsonPropertyName("totalPages")]
        public int TotalPages { get; set; }

        [JsonPropertyName("totalElements")]
        public long TotalElements { get; set; }

        [JsonPropertyName("size")]
        public int Size { get; set; }

        [JsonPropertyName("number")]
        public int Number { get; set; }
    }
}
