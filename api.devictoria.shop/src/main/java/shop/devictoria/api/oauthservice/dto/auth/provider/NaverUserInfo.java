package shop.devictoria.api.dto.auth.provider;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class NaverUserInfo {
    @JsonProperty("resultcode")
    private String resultCode;
    
    @JsonProperty("message")
    private String message;
    
    @JsonProperty("response")
    private Response response;
    
    @Getter
    @Setter
    @NoArgsConstructor
    public static class Response {
        private String id;
        private String email;
        private String name;
        private String nickname;
        
        @JsonProperty("profile_image")
        private String profileImage;
        
        private String age;
        private String gender;
        private String birthday;
        private String mobile;
    }
}

