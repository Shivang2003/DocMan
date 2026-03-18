package docman.dto;

import lombok.Data;

@Data
public class UploadRequest {
    private String username;
    private String repo;
    private String branch;
    private String projectname;
    private String index_name;
    private String embed_model;
}