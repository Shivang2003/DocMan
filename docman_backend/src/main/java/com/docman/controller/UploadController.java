package docman.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import docman.dto.UploadRequest;
import docman.service.SupabaseStorageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/docman")
public class UploadController {

    @Autowired
    private SupabaseStorageService storageService;

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> uploadFile(
            @RequestPart("payload") String payloadJson,
            @RequestPart("file") MultipartFile file
    ) throws Exception {

        ObjectMapper mapper = new ObjectMapper();
        UploadRequest payload = mapper.readValue(payloadJson, UploadRequest.class);

        String url = storageService.uploadFile(payload.getProjectname(), file);

        return ResponseEntity.ok(Map.of(
                "message", "File uploaded successfully",
                "downloadUrl", url
        ));
    }
}