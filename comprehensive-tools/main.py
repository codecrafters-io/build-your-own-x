from spider import WebSpider
from system_tools import SystemTools

def print_menu():
    print('=' * 60)
    print('综合工具集合')
    print('=' * 60)
    print('1. 网络爬虫工具')
    print('2. 系统管理工具')
    print('0. 退出')
    print('=' * 60)

def spider_menu():
    spider = WebSpider()
    
    while True:
        print('\n网络爬虫工具')
        print('1. 开始爬取')
        print('2. 设置代理')
        print('3. 设置爬取深度')
        print('0. 返回主菜单')
        
        choice = input('请选择: ')
        
        if choice == '1':
            url = input('请输入起始URL: ')
            rules_input = input('是否设置爬取规则? (y/n): ')
            
            rules = None
            if rules_input.lower() == 'y':
                rules = []
                while True:
                    selector = input('请输入CSS选择器: ')
                    extract_input = input('是否设置提取规则? (y/n): ')
                    
                    extract = {}
                    if extract_input.lower() == 'y':
                        while True:
                            key = input('请输入字段名: ')
                            extractor = input('请输入提取方式 (text 或 attr:属性名): ')
                            extract[key] = extractor
                            
                            more = input('是否添加更多提取规则? (y/n): ')
                            if more.lower() != 'y':
                                break
                    
                    rules.append({'selector': selector, 'extract': extract})
                    
                    more_rule = input('是否添加更多爬取规则? (y/n): ')
                    if more_rule.lower() != 'y':
                        break
            
            data = spider.crawl(url, rules)
            
            if data:
                save_input = input('是否保存数据? (y/n): ')
                if save_input.lower() == 'y':
                    format = input('保存格式 (json/csv): ')
                    filename = input('请输入文件名: ')
                    
                    if format.lower() == 'json':
                        spider.save_to_json(data, filename + '.json')
                        print(f'数据已保存到 {filename}.json')
                    elif format.lower() == 'csv':
                        spider.save_to_csv(data, filename + '.csv')
                        print(f'数据已保存到 {filename}.csv')
        
        elif choice == '2':
            proxy = input('请输入代理地址 (格式: http://ip:port): ')
            spider.set_proxies({'http': proxy, 'https': proxy})
            print('代理设置成功')
        
        elif choice == '3':
            depth = int(input('请输入爬取深度: '))
            spider.set_max_depth(depth)
            print('爬取深度设置成功')
        
        elif choice == '0':
            break
        
        else:
            print('无效选择，请重新输入')

def system_tools_menu():
    system_tools = SystemTools()
    
    while True:
        print('\n系统管理工具')
        print('1. 批量删除文本文件')
        print('2. 删除指定文件')
        print('3. 关闭系统')
        print('4. 重启系统')
        print('0. 返回主菜单')
        
        choice = input('请选择: ')
        
        if choice == '1':
            directory = input('请输入目录路径: ')
            force = input('是否强制删除 (y/n): ').lower() == 'y'
            result = system_tools.batch_delete_text_files(directory, force)
            print(f'成功删除: {len(result["deleted"])} 个文件')
            print(f'失败: {len(result["failed"])} 个文件')
            if result["failed"]:
                print('失败列表:')
                for file, error in result["failed"]:
                    print(f'  - {file}: {error}')
        
        elif choice == '2':
            files = input('请输入文件路径，多个文件用逗号分隔: ').split(',')
            files = [f.strip() for f in files]
            force = input('是否强制删除 (y/n): ').lower() == 'y'
            result = system_tools.delete_files(files, force)
            print(f'成功删除: {len(result["deleted"])} 个文件')
            print(f'失败: {len(result["failed"])} 个文件')
            if result["failed"]:
                print('失败列表:')
                for file, error in result["failed"]:
                    print(f'  - {file}: {error}')
        
        elif choice == '3':
            timeout = int(input('请输入延迟时间 (秒，0表示立即): '))
            force = input('是否强制关闭 (y/n): ').lower() == 'y'
            system_tools.shutdown_system(force, timeout)
        
        elif choice == '4':
            timeout = int(input('请输入延迟时间 (秒，0表示立即): '))
            force = input('是否强制重启 (y/n): ').lower() == 'y'
            system_tools.restart_system(force, timeout)
        
        elif choice == '0':
            break
        
        else:
            print('无效选择，请重新输入')

def main():
    while True:
        print_menu()
        choice = input('请选择: ')
        
        if choice == '1':
            spider_menu()
        elif choice == '2':
            system_tools_menu()
        elif choice == '0':
            print('感谢使用，再见！')
            break
        else:
            print('无效选择，请重新输入')

if __name__ == '__main__':
    main()
