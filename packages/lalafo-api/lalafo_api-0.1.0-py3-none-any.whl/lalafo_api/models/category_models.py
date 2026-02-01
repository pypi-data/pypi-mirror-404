from typing import List, Optional, Union, Iterator
from pydantic import BaseModel, HttpUrl


class Category(BaseModel):
    """Модель категории"""
    id: int
    parent_id: int
    name: str
    search_names: List[str] = []
    api_list_type: int = 1
    order: int
    ads_count: int
    children: List['Category'] = []
    url: str
    depth: int
    show_price: bool = True
    feed_type: str = "default"
    posting_type: str = "default"
    panel_type: str = "params"
    is_duplicate: bool = False
    active: bool = True
    singular_name: str
    
    def __iter__(self) -> Iterator['Category']:
        """Итерация по всем категориям поддерева (включая текущую)"""
        yield self
        for child in self.children:
            yield from child

    def find_by_id(self, category_id: int) -> Optional['Category']:
        """
        Найти категорию по ID в поддереве
        
        Args:
            category_id: ID искомой категории
            
        Returns:
            Найденная категория или None
        """
        if self.id == category_id:
            return self
        
        for child in self.children:
            found = child.find_by_id(category_id)
            if found:
                return found
        
        return None

    def find_by_name(self, name: str, case_sensitive: bool = False) -> List['Category']:
        """
        Найти категории по названию в поддереве
        
        Args:
            name: Название или часть названия
            case_sensitive: Учитывать регистр
            
        Returns:
            Список найденных категорий
        """
        results = []
        
        if case_sensitive:
            if name in self.name:
                results.append(self)
        else:
            if name.lower() in self.name.lower():
                results.append(self)
        
        for child in self.children:
            results.extend(child.find_by_name(name, case_sensitive))
        
        return results

    def find_by_alias(self, alias: str) -> List['Category']:
        """
        Найти категории по алиасу (последней части URL)
        
        Args:
            alias: Алиас категории (например, 'mobilnye-telefony')
            
        Returns:
            Список найденных категорий
        """
        results = []
        
        category_alias = self.url.strip('/').split('/')[-1]
        
        if category_alias == alias:
            results.append(self)
        
        for child in self.children:
            results.extend(child.find_by_alias(alias))
        
        return results

    def find_by_path(self, path_parts: List[str]) -> Optional['Category']:
        """
        Найти категорию по пути (списку алиасов)
        
        Args:
            path_parts: Части пути (например, ['mobilnye-telefony', 'apple'])
            
        Returns:
            Найденная категория или None
        """
        if not path_parts:
            return self
        
        current_alias = self.url.strip('/').split('/')[-1]
        
        if current_alias != path_parts[0]:
            return None
        
        if len(path_parts) == 1:
            return self
        
        remaining_parts = path_parts[1:]
        for child in self.children:
            found = child.find_by_path(remaining_parts)
            if found:
                return found
        
        return None

    def get_ancestors(self, root_categories: Optional[List['Category']] = None) -> List['Category']:
        """
        Получить всех предков категории
        
        Args:
            root_categories: Корневые категории для поиска цепочки
            
        Returns:
            Список категорий от корня до родителя текущей категории
        """
        ancestors = []
        
        def find_path_to_parent(current, target_id, path):
            if current.id == target_id:
                return path + [current]
            
            for child in current.children:
                result = find_path_to_parent(child, target_id, path + [current])
                if result:
                    return result
            
            return None
        
        if root_categories:
            for root in root_categories:
                path = find_path_to_parent(root, self.id, [])
                if path:
                    return path[:-1]
        
        return ancestors

    @property
    def alias(self) -> str:
        """Алиас категории (последняя часть URL)"""
        return self.url.strip('/').split('/')[-1]

    @property
    def path_aliases(self) -> List[str]:
        """Все алиасы в пути категории"""
        return self.url.strip('/').split('/')

    @property
    def is_leaf(self) -> bool:
        """Является ли категория листовой (без детей)"""
        return len(self.children) == 0

    @property
    def breadcrumbs(self) -> List[str]:
        """Хлебные крошки (иерархия названий)"""
        crumbs = []
        
        def collect_crumbs(cat):
            if cat.children:
                for child in cat.children:
                    if child.id == self.id or any(c.id == self.id for c in child):
                        crumbs.append(cat.name)
                        collect_crumbs(child)
                        break
        
        return [self.name]

    def print_tree(self, indent: int = 0, max_depth: Optional[int] = None) -> str:
        """
        Красивое дерево категорий
        
        Args:
            indent: Начальный отступ
            max_depth: Максимальная глубина отображения
            
        Returns:
            Строка с деревом
        """
        if max_depth is not None and indent // 2 >= max_depth:
            return ""
        
        result = []
        prefix = "  " * indent
        
        if indent == 0:
            icon = "🌳"
        elif self.is_leaf:
            icon = "🍃"
        else:
            icon = "🌿"
        
        result.append(f"{prefix}{icon} {self.name} (id: {self.id}, ads: {self.ads_count})")
        
        for child in self.children:
            result.append(child.print_tree(indent + 1, max_depth))
        
        return "\n".join(filter(None, result))