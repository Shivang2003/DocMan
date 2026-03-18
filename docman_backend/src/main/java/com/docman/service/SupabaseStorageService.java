package docman.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

@Service
public class SupabaseStorageService {

    @Value("${supabase.url}")
    private String supabaseUrl;

    @Value("${supabase.serviceKey}")
    private String serviceRoleKey;

    @Value("${supabase.bucket}")
    private String bucketName;

    public String uploadFile(String projectName, MultipartFile file) throws Exception {

        String filePath = "docs/raw/" + projectName + "/" + file.getOriginalFilename();

        String uploadUrl = supabaseUrl + "/storage/v1/object/" + bucketName + "/" + filePath;

        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer " + serviceRoleKey);
        headers.set("Content-Type", file.getContentType());

        HttpEntity<byte[]> requestEntity = new HttpEntity<>(file.getBytes(), headers);

        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.exchange(
                uploadUrl,
                HttpMethod.POST,
                requestEntity,
                String.class
        );

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new RuntimeException("Upload failed: " + response.getBody());
        }

        return supabaseUrl + "/storage/v1/object/public/" + bucketName + "/" + filePath;
    }
}

// send file FE / Create direcgtor  se ->  toh payload aayega jo hai abhi toh usme directory mentioned hogi indexname and projecgt name type se same hoga ya key pair ya phir is project ka ye porjecti ndex hai types toh fe se aaye toh wo saath me project index na