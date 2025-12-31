#ifndef _CPA_REPOSITORY_IMPL_H_
#define _CPA_REPOSITORY_IMPL_H_

#include "../CpaRepository.h"
#include "../IFileManager.h"
#include <optional>

#define DATABASE_PATH "/Users/nkurude/Downloads/db"

template<typename Entity, typename ID>
class CpaRepositoryImpl : public CpaRepository<Entity, ID> {
    Public Virtual ~CpaRepositoryImpl() = default;

    AUTOWIRED
    Protected IFileManagerPtr fileManager;

    // Helper method to construct file path
    Protected StdString GetFilePath(const StdString& entityName, ID id) {
        return StdString(DATABASE_PATH) + "/" + entityName + "_" + StdString(std::to_string(id).c_str()) + ".txt";
    }

    // Create: Save a new entity
    Public Virtual Entity Save(Entity& entity) override {
        // Get entity name (static method)
        StdString entityName = Entity::GetPrimaryKeyName();
        
        // Get generated ID (non-static method)
        ID generatedId = entity.GetPrimaryKey();
        
        // Construct file path: DATABASE_PATH/EntityName_GeneratedID.txt
        StdString filePath = GetFilePath(entityName, generatedId);
        
        // Serialize entity (non-static method)
        StdString contents = entity.Serialize();
        
        // Save to file using file manager
        CStdString filePathRef = filePath;
        CStdString contentsRef = contents;
        fileManager->Create(filePathRef, contentsRef);
        
        return entity;
    }

    // Read: Find entity by ID
    Public Virtual optional<Entity> FindById(ID& id) override {
        // Get entity name (static method)
        StdString entityName = Entity::GetPrimaryKeyName();
        
        // Construct file path
        StdString filePath = GetFilePath(entityName, id);
        
        // Read file contents
        CStdString filePathRef = filePath;
        StdString contents = fileManager->Read(filePathRef);
        
        // Check if file was read successfully (non-empty content)
        if (contents.empty()) {
            return std::nullopt;
        }
        
        // Deserialize entity
        Entity entity;
        entity.Deserialize(contents);
        
        return entity;
    }

    // Read: Find all entities
    Public Virtual vector<Entity> FindAll() override {
        return vector<Entity>();
    }

    // Update: Update an existing entity
    Public Virtual Entity Update(Entity& entity) override {
        // Get entity name (static method)
        StdString entityName = Entity::GetPrimaryKeyName();
        
        // Get ID from entity
        ID id = entity.GetPrimaryKey();
        
        // Construct file path
        StdString filePath = GetFilePath(entityName, id);
        
        // Serialize entity
        StdString contents = entity.Serialize();
        
        // Update file using file manager
        CStdString filePathRef = filePath;
        CStdString contentsRef = contents;
        fileManager->Update(filePathRef, contentsRef);
        
        return entity;
    }

    // Delete: Delete entity by ID
    Public Virtual Void DeleteById(ID& id) override {
        // Get entity name (static method)
        StdString entityName = Entity::GetPrimaryKeyName();
        
        // Construct file path
        StdString filePath = GetFilePath(entityName, id);
        
        // Delete file using file manager
        CStdString filePathRef = filePath;
        fileManager->Delete(filePathRef);
    }

    // Delete: Delete an entity
    Public Virtual Void Delete(Entity& entity) override {
        // Get ID from entity
        ID id = entity.GetPrimaryKey();
        
        // Use DeleteById to delete
        DeleteById(id);
    }

    // Check if entity exists by ID
    Public Virtual Bool ExistsById(ID& id) override {
        // Get entity name (static method)
        StdString entityName = Entity::GetPrimaryKeyName();
        
        // Construct file path
        StdString filePath = GetFilePath(entityName, id);
        
        // Try to read the file - if it returns non-empty, it exists
        CStdString filePathRef = filePath;
        StdString contents = fileManager->Read(filePathRef);
        
        return !contents.empty();
    }
};

#endif // _CPA_REPOSITORY_IMPL_H_   