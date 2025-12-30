#ifndef _CPA_REPOSITORY_IMPL_H_
#define _CPA_REPOSITORY_IMPL_H_

#include "../CpaRepository.h"
#include <iostream>

template<typename Entity, typename ID>
class CpaRepositoryImpl : public virtual CpaRepository<Entity, ID> {
    Public Virtual ~CpaRepositoryImpl() = default;

    // Dummy implementations that print method names
    Public Virtual Entity Save(Entity& entity) override {
        std::cout << "CpaRepositoryImpl::Save" << std::endl;
        return entity;
    }

    Public Virtual optional<Entity> FindById(ID& id) override {
        std::cout << "CpaRepositoryImpl::FindById" << std::endl;
        return std::nullopt;
    }

    Public Virtual vector<Entity> FindAll() override {
        std::cout << "CpaRepositoryImpl::FindAll" << std::endl;
        return vector<Entity>();
    }

    Public Virtual Entity Update(Entity& entity) override {
        std::cout << "CpaRepositoryImpl::Update" << std::endl;
        return entity;
    }

    Public Virtual Void DeleteById(ID& id) override {
        std::cout << "CpaRepositoryImpl::DeleteById" << std::endl;
    }

    Public Virtual Void Delete(Entity& entity) override {
        std::cout << "CpaRepositoryImpl::Delete" << std::endl;
    }

    Public Virtual Bool ExistsById(ID& id) override {
        std::cout << "CpaRepositoryImpl::ExistsById" << std::endl;
        return false;
    }
};

#endif // _CPA_REPOSITORY_IMPL_H_   