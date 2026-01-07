package shop.devictoria.api.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import shop.devictoria.api.domain.SocialProvider;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SocialLoginRequest {

    @NotNull(message = "소셜 로그인 제공자는 필수입니다")
    private SocialProvider provider;

    @NotBlank(message = "소셜 로그인 제공자 ID는 필수입니다")
    private String providerId;

    @NotBlank(message = "이메일은 필수입니다")
    @Email(message = "올바른 이메일 형식이 아닙니다")
    private String email;

    @NotBlank(message = "이름은 필수입니다")
    private String name;

    private String profileImage;

    private String phoneNumber;
}

