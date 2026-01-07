package shop.devictoria.api.dto.auth;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class NaverLoginRequest {
    private String authorizationCode;
    private String accessToken;
    private String email;
    private String nickname;
    private String state;  // 네이버 state 파라미터
}

