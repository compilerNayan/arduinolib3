#ifndef _CPA_REPOSITORY_IMPL_H_
#define _CPA_REPOSITORY_IMPL_H_

#include "../CpaRepository.h"

template<typename Entity, typename ID>
class CpaRepositoryImpl : public CpaRepository<Entity, ID> {
    Public Virtual ~CpaRepositoryImpl() = default;
};

#endif // _CPA_REPOSITORY_IMPL_H_   