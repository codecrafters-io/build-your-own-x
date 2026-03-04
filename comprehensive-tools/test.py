from spider import WebSpider
from system_tools import SystemTools

# 测试网络爬虫
def test_spider():
    print('测试网络爬虫...')
    spider = WebSpider()
    spider.set_max_depth(1)
    
    # 测试简单爬取
    url = 'https://example.com'
    data = spider.crawl(url)
    print(f'爬取到 {len(data)} 条数据')
    
    # 测试带规则的爬取
    rules = [{
        'selector': 'a',
        'extract': {
            'text': 'text',
            'href': 'attr:href'
        }
    }]
    data_with_rules = spider.crawl(url, rules)
    print(f'带规则爬取到 {len(data_with_rules)} 条数据')
    
    # 测试保存功能
    if data_with_rules:
        spider.save_to_json(data_with_rules, 'test_spider.json')
        spider.save_to_csv(data_with_rules, 'test_spider.csv')
        print('数据已保存到 test_spider.json 和 test_spider.csv')

# 测试系统管理工具
def test_system_tools():
    print('\n测试系统管理工具...')
    system_tools = SystemTools()
    
    # 创建测试文件
    with open('test_file.txt', 'w') as f:
        f.write('测试文件')
    
    # 测试删除文件
    result = system_tools.delete_files(['test_file.txt'], force=True)
    print(f'删除文件结果: {result}')

if __name__ == '__main__':
    test_spider()
    test_system_tools()
    print('\n测试完成！')
